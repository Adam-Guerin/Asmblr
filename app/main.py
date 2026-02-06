from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Response
from fastapi.responses import FileResponse
from uuid import uuid4
from pathlib import Path
from pydantic import BaseModel, Field
from pathlib import Path
import time
import httpx

from app.core.config import get_settings
from app.core.pipeline import VenturePipeline
from app.core.llm import check_ollama
from app.core.logging import setup_logging, set_log_context, clear_log_context
from app.core.metrics import METRICS
from app.core.metrics_prom import PROM_METRICS
from app.core.rate_limit import RateLimiter
from app.core.audit import write_audit_event
from app.core.jobs import enqueue_run, enqueue_resume, get_job_status
from app.core.models import SeedInputs
from app.core.deploy import deploy_run

setup_logging()
settings = get_settings()
pipeline = VenturePipeline(settings)
app = FastAPI(title="AI Venture Factory")
run_limiter = RateLimiter(settings.run_rate_limit_per_min, settings.run_rate_limit_burst)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    request_id = request.headers.get("X-Request-Id", str(uuid4()))
    set_log_context(request_id=request_id)
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.time() - start) * 1000
        METRICS.record_api(request.url.path, 500, duration_ms)
        PROM_METRICS.record_api(request.url.path, "500", duration_ms)
        clear_log_context()
        raise
    duration_ms = (time.time() - start) * 1000
    METRICS.record_api(request.url.path, response.status_code, duration_ms)
    PROM_METRICS.record_api(request.url.path, str(response.status_code), duration_ms)
    response.headers["X-Request-Id"] = request_id
    clear_log_context()
    return response


def _require_api_key(request: Request) -> None:
    if not settings.api_key:
        return
    provided = request.headers.get("X-API-Key", "")
    if provided != settings.api_key and (not settings.api_key_prev or provided != settings.api_key_prev):
        raise HTTPException(status_code=401, detail="Unauthorized")


class RunRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    n_ideas: int | None = Field(default=None, ge=1, le=20)
    fast: bool = False
    theme: str | None = Field(default=None, max_length=120)
    seed_icp: str | None = Field(default=None, max_length=400)
    seed_pains: list[str] | None = None
    seed_competitors: list[str] | None = None
    seed_context: str | None = Field(default=None, max_length=1000)
    webhook_url: str | None = Field(default=None, max_length=300)
    deploy: bool = False
    deploy_dry_run: bool = True


class FeedbackMetricsRequest(BaseModel):
    ctr_landing: float = Field(..., ge=0)
    signup_rate: float = Field(..., ge=0)
    activation_rate: float = Field(..., ge=0)
    visitors: int | None = Field(default=None, ge=0)
    signups: int | None = Field(default=None, ge=0)
    activated_users: int | None = Field(default=None, ge=0)
    window_days: int | None = Field(default=None, ge=1, le=365)
    notes: str | None = Field(default=None, max_length=400)


def _normalize_seed_list(value: list[str] | None) -> list[str]:
    if not value:
        return []
    trimmed = [item.strip() for item in value if item and item.strip()]
    return trimmed[:12]


def _notify_webhook(url: str, payload: dict) -> None:
    try:
        timeout = httpx.Timeout(5.0, connect=3.0, read=5.0, write=5.0, pool=3.0)
        with httpx.Client(timeout=timeout) as client:
            client.post(url, json=payload)
    except Exception:
        return


@app.post("/run")
def start_run(req: RunRequest, background: BackgroundTasks, request: Request):
    _require_api_key(request)
    limiter_key = settings.api_key or (request.client.host if request.client else "unknown")
    if not run_limiter.allow(limiter_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for run creation")
    run_id = pipeline.manager.create_run(req.topic)
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_start",
            "run_id": run_id,
            "topic": req.topic,
            "n_ideas": req.n_ideas,
            "fast": req.fast,
            "theme": req.theme,
            "seed_icp": req.seed_icp,
            "seed_pains": req.seed_pains,
            "seed_competitors": req.seed_competitors,
            "seed_context": req.seed_context,
            "webhook": bool(req.webhook_url),
            "actor": request.headers.get("X-Actor", "api"),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        },
    )
    if req.webhook_url:
        try:
            pipeline.manager.set_webhook(run_id, req.webhook_url)
        except Exception:
            pass
    try:
        pipeline._ensure_llm_ready(run_id)
    except Exception as exc:
        pipeline.record_ollama_failure(run_id, exc)
        raise HTTPException(status_code=503, detail=f"Ollama not ready: {exc}")
    n_ideas = req.n_ideas or settings.default_n_ideas
    if len(req.topic) > 200:
        raise HTTPException(status_code=422, detail="Topic too long")
    seeds = SeedInputs(
        icp=req.seed_icp,
        pains=_normalize_seed_list(req.seed_pains),
        competitors=_normalize_seed_list(req.seed_competitors),
        context=req.seed_context,
        theme=req.theme,
    )

    job_id = enqueue_run(
        run_id=run_id,
        topic=req.topic,
        n_ideas=n_ideas,
        fast=req.fast,
        seeds=seeds,
        webhook_url=req.webhook_url,
        deploy=req.deploy,
        deploy_dry_run=req.deploy_dry_run,
    )
    pipeline.manager.update_status(run_id, "queued")
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_queued",
            "run_id": run_id,
            "job_id": job_id,
            "actor": request.headers.get("X-Actor", "api"),
        },
    )
    return {"run_id": run_id, "status": "queued", "job_id": job_id, "webhook": bool(req.webhook_url)}


@app.post("/run/{run_id}/resume")
def resume_run(run_id: str, background: BackgroundTasks, request: Request):
    _require_api_key(request)
    limiter_key = settings.api_key or (request.client.host if request.client else "unknown")
    if not run_limiter.allow(limiter_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for run resume")
    run = pipeline.manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_resume",
            "run_id": run_id,
            "topic": run.get("topic"),
            "actor": request.headers.get("X-Actor", "api"),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        },
    )

    job_id = enqueue_resume(run_id=run_id)
    pipeline.manager.update_status(run_id, "queued")
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_resume_queued",
            "run_id": run_id,
            "job_id": job_id,
            "actor": request.headers.get("X-Actor", "api"),
        },
    )
    return {"run_id": run_id, "status": "queued", "job_id": job_id}

@app.get("/run/{run_id}")
def get_run(run_id: str, request: Request):
    _require_api_key(request)
    run = pipeline.manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/run/{run_id}/artifact/{name}")
def get_artifact(run_id: str, name: str, request: Request):
    _require_api_key(request)
    run = pipeline.manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    output_dir = Path(run["output_dir"])
    if ".." in name or name.startswith(("/", "\\")):
        raise HTTPException(status_code=400, detail="Invalid artifact name")
    allowed = {"top_idea.md", "market_report.md", "prd.md", "tech_spec.md", "launch_checklist.md", "decision.md"}
    if name not in allowed:
        raise HTTPException(status_code=400, detail="Artifact not allowed")
    target = output_dir / name
    if not target.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(str(target))


@app.get("/run/{run_id}/progress")
def get_progress(run_id: str, request: Request):
    _require_api_key(request)
    run = pipeline.manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    output_dir = Path(run["output_dir"])
    log_path = output_dir / "progress.log"
    if not log_path.exists():
        return {"run_id": run_id, "log": ""}
    return {"run_id": run_id, "log": log_path.read_text(encoding="utf-8", errors="ignore")}


@app.get("/run/{run_id}/job")
def get_run_job(run_id: str, request: Request):
    _require_api_key(request)
    run = pipeline.manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "job": get_job_status(run_id)}


@app.post("/run/{run_id}/feedback-metrics")
def record_feedback_metrics(run_id: str, req: FeedbackMetricsRequest, request: Request):
    _require_api_key(request)
    run = pipeline.manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        payload = pipeline.record_product_feedback(
            run_id=run_id,
            ctr_landing=req.ctr_landing,
            signup_rate=req.signup_rate,
            activation_rate=req.activation_rate,
            visitors=req.visitors,
            signups=req.signups,
            activated_users=req.activated_users,
            window_days=req.window_days,
            notes=req.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_feedback_metrics",
            "run_id": run_id,
            "topic": run.get("topic"),
            "actor": request.headers.get("X-Actor", "api"),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
            "learning_score": payload.get("learning_score"),
            "confidence": payload.get("confidence"),
        },
    )
    return {"run_id": run_id, "status": "recorded", "metrics": payload}


@app.post("/run/{run_id}/deploy")
def deploy_run_endpoint(run_id: str, request: Request, dry_run: bool = False):
    _require_api_key(request)
    if not settings.enable_deploy and not dry_run:
        raise HTTPException(status_code=400, detail="Deploy disabled (ENABLE_DEPLOY=false)")
    try:
        result = deploy_run(settings, run_id, dry_run=dry_run)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {
        "run_id": run_id,
        "ok": result.ok,
        "message": result.message,
        "deploy_log": str(result.deploy_log),
        "deployed_url": str(result.deployed_url) if result.deployed_url else None,
    }


@app.get("/metrics")
def get_metrics(request: Request):
    _require_api_key(request)
    return METRICS.snapshot()


@app.get("/metrics/prometheus")
def get_prometheus_metrics(request: Request):
    _require_api_key(request)
    payload = PROM_METRICS.render()
    return Response(content=payload, media_type=PROM_METRICS.content_type)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    errors = []
    for general_model, code_model in pipeline._model_candidates():
        try:
            check_ollama(settings.ollama_base_url, [general_model, code_model])
            return {"status": "ready", "general_model": general_model, "code_model": code_model}
        except Exception as exc:
            errors.append(str(exc))
    reason = errors[-1] if errors else "No model pair available"
    raise HTTPException(status_code=503, detail=f"Ollama not ready: {reason}")
