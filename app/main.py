from fastapi import FastAPI, BackgroundTasks, HTTPException, Request, Response
from fastapi.responses import FileResponse
from uuid import uuid4
from pathlib import Path
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional
import time
import httpx
import json

from app.core.config import get_settings, previous_secret_allowed, validate_prod_mode
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
from app.mvp.orchestrator import create_custom_mvp
from app.mvp.ceo_orchestrator import execute_ceo_vision

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
    if provided == settings.api_key:
        return
    if settings.api_key_prev and provided == settings.api_key_prev:
        prev_allowed, reason = previous_secret_allowed(
            previous_value=settings.api_key_prev,
            current_value=settings.api_key,
            expires_at=settings.api_key_prev_expires_at,
            enforce_rotation=settings.enforce_key_rotation,
        )
        if prev_allowed:
            return
        raise HTTPException(status_code=401, detail=f"Unauthorized (previous key {reason})")
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
    execution_profile: str | None = Field(default=None, max_length=20)


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


def _normalize_execution_profile(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().lower()
    if cleaned in {"quick", "standard", "deep"}:
        return cleaned
    raise HTTPException(status_code=422, detail="execution_profile must be one of: quick, standard, deep")


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
            "execution_profile": req.execution_profile,
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
    execution_profile = _normalize_execution_profile(req.execution_profile)

    job_id = enqueue_run(
        run_id=run_id,
        topic=req.topic,
        n_ideas=n_ideas,
        fast=req.fast,
        seeds=seeds,
        webhook_url=req.webhook_url,
        deploy=req.deploy,
        deploy_dry_run=req.deploy_dry_run,
        execution_profile=execution_profile,
    )
    pipeline.manager.update_status(run_id, "queued")
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_queued",
            "run_id": run_id,
            "job_id": job_id,
            "execution_profile": execution_profile,
            "actor": request.headers.get("X-Actor", "api"),
        },
    )
    return {
        "run_id": run_id,
        "status": "queued",
        "job_id": job_id,
        "webhook": bool(req.webhook_url),
        "execution_profile": execution_profile or ("quick" if req.fast else "standard"),
    }


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


@app.get("/health")
async def health():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/health/detailed")
async def health_detailed():
    """Comprehensive health check with all system components"""
    import asyncio
    from app.core.config import get_settings
    from pathlib import Path
    
    settings = get_settings()
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        # Test database connection
        db_path = Path(settings.data_dir) / "app.db"
        if db_path.exists():
            health_status["checks"]["database"] = {
                "status": "healthy",
                "path": str(db_path),
                "size_mb": round(db_path.stat().st_size / (1024*1024), 2)
            }
        else:
            health_status["checks"]["database"] = {
                "status": "warning",
                "message": "Database file not found"
            }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Redis connectivity
    try:
        import redis
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "url": settings.redis_url
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check Ollama connectivity
    try:
        ollama_status = await check_ollama(settings.ollama_base_url)
        health_status["checks"]["ollama"] = {
            "status": "healthy" if ollama_status else "unhealthy",
            "url": settings.ollama_base_url,
            "models_available": ollama_status
        }
    except Exception as e:
        health_status["checks"]["ollama"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(settings.runs_dir)
        free_percent = (free / total) * 100
        health_status["checks"]["disk_space"] = {
            "status": "healthy" if free_percent > 10 else "warning" if free_percent > 5 else "unhealthy",
            "free_gb": round(free / (1024**3), 2),
            "free_percent": round(free_percent, 2)
        }
    except Exception as e:
        health_status["checks"]["disk_space"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check runs directory
    try:
        runs_path = Path(settings.runs_dir)
        if runs_path.exists():
            run_count = len([d for d in runs_path.iterdir() if d.is_dir()])
            health_status["checks"]["runs_directory"] = {
                "status": "healthy",
                "path": str(runs_path),
                "run_count": run_count
            }
        else:
            health_status["checks"]["runs_directory"] = {
                "status": "warning",
                "message": "Runs directory not found"
            }
    except Exception as e:
        health_status["checks"]["runs_directory"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check pipeline status
    try:
        health_status["checks"]["pipeline"] = {
            "status": "healthy",
            "max_concurrent_runs": settings.run_max_concurrent,
            "rate_limit_per_min": settings.run_rate_limit_per_min
        }
    except Exception as e:
        health_status["checks"]["pipeline"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Determine overall status
    unhealthy_checks = [k for k, v in health_status["checks"].items() if v.get("status") == "unhealthy"]
    warning_checks = [k for k, v in health_status["checks"].items() if v.get("status") == "warning"]
    
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
        health_status["summary"] = f"Unhealthy checks: {', '.join(unhealthy_checks)}"
    elif warning_checks:
        health_status["status"] = "warning"
        health_status["summary"] = f"Warning checks: {', '.join(warning_checks)}"
    else:
        health_status["summary"] = "All checks passed"
    
    return health_status


@app.get("/readyz")
async def readyz():
    """Readiness check - indicates if the service is ready to handle traffic"""
    try:
        # Check critical dependencies
        settings = get_settings()
        
        # Check database
        db_path = Path(settings.data_dir) / "app.db"
        if not db_path.exists():
            raise Exception("Database not found")
        
        # Check Ollama models
        errors = []
        for general_model, code_model in pipeline._model_candidates():
            try:
                ollama_status = await check_ollama(settings.ollama_base_url, [general_model, code_model])
                if ollama_status:
                    return {
                        "status": "ready", 
                        "timestamp": time.time(),
                        "general_model": general_model, 
                        "code_model": code_model
                    }
            except Exception as exc:
                errors.append(str(exc))
        
        # Production mode checks
        if settings.prod_mode and settings.require_prod_checklist:
            prod_checks = validate_prod_mode(settings)
            if not prod_checks.get("ok"):
                failing = next((item for item in prod_checks.get("checks", []) if not item.get("ok")), None)
                detail = failing.get("detail") if failing else "Production checklist failed"
                raise HTTPException(status_code=503, detail=f"Prod checklist failed: {detail}")
        
        raise Exception(f"Ollama models not ready: {'; '.join(errors)}")
        
    except Exception as e:
        return {
            "status": "not_ready", 
            "timestamp": time.time(),
            "error": str(e)
        }


class CustomMVPRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="L'idée à développer en MVP")
    seed_inputs: Optional[SeedInputs] = Field(None, description="Inputs utilisateur optionnels")
    fast_mode: bool = Field(False, description="Mode rapide pour les tests")


class CEOVisionRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="L'idée à dominer en tant que CEO")
    seed_inputs: Optional[SeedInputs] = Field(None, description="Inputs utilisateur optionnels")
    risk_level: str = Field("EXTREME", description="Niveau de risque CEO (LOW/MEDIUM/HIGH/EXTREME)")
    timeline_aggression: str = Field("INSANE", description="Aggressivité timeline (CONSERVATIVE/NORMAL/AGGRESSIVE/INSANE)")
    unleash_ceo: bool = Field(True, description="Activer le mode CEO sans limites")


@app.post("/mvp/custom")
async def create_mvp_custom(req: CustomMVPRequest, background: BackgroundTasks, request: Request):
    """
    Crée un MVP 100% customisé avec orchestrateur intelligent
    
    Endpoint principal pour la création de MVP personnalisés.
    L'orchestrateur analyse l'idée, génère des prompts customisés,
    et orchestre les agents developer pour un résultat optimal.
    """
    _require_api_key(request)
    
    # Validation rate limit
    limiter_key = settings.api_key or (request.client.host if request.client else "unknown")
    if not run_limiter.allow(limiter_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded for MVP creation")
    
    # Générer un run_id unique
    run_id = str(uuid4())
    run_dir = Path(settings.runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Logger la demande
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "custom_mvp_started",
            "run_id": run_id,
            "topic": req.topic,
            "fast_mode": req.fast_mode,
            "actor": request.headers.get("X-Actor", "api"),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        },
    )
    
    # Démarrer l'orchestration en background
    async def run_orchestration():
        try:
            from app.core.llm import LLMClient
            
            # Initialiser le client LLM
            llm_client = LLMClient(settings.ollama_base_url, settings.code_model)
            
            # Créer le MVP customisé
            result = await create_custom_mvp(
                topic=req.topic,
                settings=settings,
                llm_client=llm_client,
                run_id=run_id,
                run_dir=run_dir,
                seed_inputs=req.seed_inputs,
                fast_mode=req.fast_mode
            )
            
            # Sauvegarder les résultats
            results_file = run_dir / "custom_mvp_results.json"
            results_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            
            # Logger le succès
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "custom_mvp_completed",
                    "run_id": run_id,
                    "topic": req.topic,
                    "idea_name": result.get("orchestration_plan", {}).get("idea_name"),
                    "mobile_required": result.get("orchestration_plan", {}).get("mobile_required"),
                    "status": "success",
                },
            )
            
        except Exception as exc:
            # Logger l'erreur
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "custom_mvp_failed",
                    "run_id": run_id,
                    "topic": req.topic,
                    "error": str(exc),
                    "status": "failed",
                },
            )
            # Propager l'erreur
            raise
    
    # Ajouter la tâche en background
    background.add_task(run_orchestration)
    
    return {
        "run_id": run_id,
        "status": "orchestration_started",
        "topic": req.topic,
        "fast_mode": req.fast_mode,
        "message": "Orchestration MVP custom démarrée en background"
    }


@app.get("/mvp/custom/{run_id}")
def get_custom_mvp_status(run_id: str, request: Request):
    """Récupère le statut d'une orchestration MVP custom"""
    _require_api_key(request)
    
    run_dir = Path(settings.runs_dir) / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    
    results_file = run_dir / "custom_mvp_results.json"
    if results_file.exists():
        try:
            results = json.loads(results_file.read_text(encoding="utf-8"))
            return {
                "run_id": run_id,
                "status": "completed",
                "results": results
            }
        except Exception:
            pass
    
    # Vérifier si le processus est en cours
    progress_file = run_dir / "orchestration.log"
    if progress_file.exists():
        return {
            "run_id": run_id,
            "status": "in_progress",
            "message": "Orchestration en cours..."
        }
    
    return {
        "run_id": run_id,
        "status": "not_started",
        "message": "Orchestration pas encore démarrée"
    }


@app.get("/mvp/custom/{run_id}/download")
def download_custom_mvp(run_id: str, request: Request):
    """Télécharge le MVP customisé en ZIP"""
    _require_api_key(request)
    
    run_dir = Path(settings.runs_dir) / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    
    results_file = run_dir / "custom_mvp_results.json"
    if not results_file.exists():
        raise HTTPException(status_code=400, detail="MVP pas encore complété")
    
    # Créer un ZIP avec tous les résultats
    import zipfile
    import tempfile
    
    zip_path = run_dir / f"{run_id}_custom_mvp.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Ajouter les résultats
        zipf.write(results_file, "custom_mvp_results.json")
        
        # Ajouter le repo si existant
        repo_dir = run_dir / "mvp_repo"
        if repo_dir.exists():
            for file_path in repo_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(run_dir)
                    zipf.write(file_path, arcname)
        
        # Ajouter les autres artefacts
        for artifact in ["landing_page", "content_pack", "brand_assets"]:
            artifact_dir = run_dir / artifact
            if artifact_dir.exists():
                for file_path in artifact_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(run_dir)
                        zipf.write(file_path, arcname)
    
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"{run_id}_custom_mvp.zip"
    )


@app.post("/ceo/unleash")
async def unleash_ceo_vision(req: CEOVisionRequest, background: BackgroundTasks, request: Request):
    """
    🚀 UNLEASH CEO VISION - Exécution sans limites
    
    Endpoint CEO pour ceux qui veulent dominer leur marché.
    Pas de compromis, pas de peur, que de l'ambition démesurée.
    
    Le CEO orchestrator prend des décisions audacieuses,
    attaque les concurrents, et prépare la domination totale.
    """
    _require_api_key(request)
    
    # Validation que le CEO est prêt
    if not req.unleash_ceo:
        raise HTTPException(status_code=400, detail="CEO mode must be unleashed")
    
    # Validation rate limit (mais les CEOs n'ont pas de limites)
    limiter_key = settings.api_key or (request.client.host if request.client else "unknown")
    if not run_limiter.allow(limiter_key):
        # Les CEOs peuvent parfois contourner les limites...
        logger.warning(f"⚡ CEO {req.topic} attempting to bypass rate limits")
    
    # Générer un run_id CEO
    run_id = f"ceo_{str(uuid4())}"
    run_dir = Path(settings.runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Logger l'arrivée du CEO
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "ceo_vision_unleashed",
            "run_id": run_id,
            "topic": req.topic,
            "risk_level": req.risk_level,
            "timeline_aggression": req.timeline_aggression,
            "mindset": "UNLIMITED_CEO",
            "actor": request.headers.get("X-Actor", "ceo"),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        },
    )
    
    # Démarrer l'exécution CEO en background
    async def run_ceo_execution():
        try:
            from app.core.llm import LLMClient
            
            # Initialiser le client LLM pour le CEO
            llm_client = LLMClient(settings.ollama_base_url, settings.code_model)
            
            # Exécuter la vision CEO sans limites
            result = await execute_ceo_vision(
                topic=req.topic,
                settings=settings,
                llm_client=llm_client,
                run_id=run_id,
                run_dir=run_dir,
                seed_inputs=req.seed_inputs,
                risk_level=req.risk_level,
                timeline_aggression=req.timeline_aggression
            )
            
            # Sauvegarder les résultats CEO
            results_file = run_dir / "ceo_vision_results.json"
            results_file.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            
            # Logger le succès CEO
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "ceo_vision_executed",
                    "run_id": run_id,
                    "topic": req.topic,
                    "vision": result.get("ceo_strategy", {}).get("vision"),
                    "bold_moves": len(result.get("bold_moves_made", [])),
                    "domination_plan": result.get("domination_plan", {}).get("exit_valuation"),
                    "status": "CEO_SUCCESS",
                },
            )
            
            logger.info(f"🏆 CEO VISION DOMINATED: {req.topic}")
            
        except Exception as exc:
            # Logger l'échec CEO (mais les CEOs rebondissent toujours)
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "ceo_vision_failed",
                    "run_id": run_id,
                    "topic": req.topic,
                    "error": str(exc),
                    "status": "CEO_FAILURE",
                    "lesson": "Even bold CEOs learn from failure"
                },
            )
            logger.error(f"💥 CEO VISION CRASHED: {req.topic} - {exc}")
            raise
    
    # Ajouter la tâche CEO en background
    background.add_task(run_ceo_execution)
    
    return {
        "run_id": run_id,
        "status": "ceo_vision_unleashed",
        "topic": req.topic,
        "risk_level": req.risk_level,
        "timeline_aggression": req.timeline_aggression,
        "message": f"🚀 CEO UNLEASHED: {req.topic} - Market domination in progress...",
        "ceo_mindset": "UNLIMITED",
        "expected_outcome": "TOTAL_MARKET_DOMINATION"
    }


@app.get("/ceo/{run_id}")
def get_ceo_vision_status(run_id: str, request: Request):
    """Récupère le statut d'une vision CEO"""
    _require_api_key(request)
    
    # Vérifier si c'est un run CEO
    if not run_id.startswith("ceo_"):
        raise HTTPException(status_code=400, detail="Not a CEO run ID")
    
    run_dir = Path(settings.runs_dir) / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="CEO run not found")
    
    results_file = run_dir / "ceo_vision_results.json"
    if results_file.exists():
        try:
            results = json.loads(results_file.read_text(encoding="utf-8"))
            return {
                "run_id": run_id,
                "status": "ceo_vision_executed",
                "results": results,
                "message": "🏆 CEO vision executed - Market domination ready"
            }
        except Exception:
            pass
    
    # Vérifier si le CEO est en cours d'exécution
    progress_file = run_dir / "orchestration.log"
    if progress_file.exists():
        return {
            "run_id": run_id,
            "status": "ceo_in_execution",
            "message": "🔥 CEO executing vision - Bold moves in progress..."
        }
    
    return {
        "run_id": run_id,
        "status": "ceo_not_started",
        "message": "⏳ CEO vision not yet unleashed"
    }


@app.get("/ceo/{run_id}/download")
def download_ceo_empire(run_id: str, request: Request):
    """Télécharge l'empire CEO complet en ZIP"""
    _require_api_key(request)
    
    if not run_id.startswith("ceo_"):
        raise HTTPException(status_code=400, detail="Not a CEO run ID")
    
    run_dir = Path(settings.runs_dir) / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="CEO run not found")
    
    results_file = run_dir / "ceo_vision_results.json"
    if not results_file.exists():
        raise HTTPException(status_code=400, detail="CEO vision not yet executed")
    
    # Créer un ZIP avec tout l'empire CEO
    import zipfile
    
    zip_path = run_dir / f"{run_id}_ceo_empire.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Ajouter les résultats CEO
        zipf.write(results_file, "ceo_vision_results.json")
        
        # Ajouter le repo MVP
        repo_dir = run_dir / "mvp_repo"
        if repo_dir.exists():
            for file_path in repo_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(run_dir)
                    zipf.write(file_path, arcname)
        
        # Ajouter les autres artefacts CEO
        for artifact in ["landing_page", "content_pack", "brand_assets", "mobile"]:
            artifact_dir = run_dir / artifact
            if artifact_dir.exists():
                for file_path in artifact_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(run_dir)
                        zipf.write(file_path, arcname)
        
        # Ajouter un README CEO spécial
        ceo_readme = run_dir / "CEO_EMPIRE_README.md"
        if not ceo_readme.exists():
            ceo_content = f"""# 🏆 CEO Empire - {run_id}

## Vision CEO
Ce projet a été exécuté avec une mentalité CEO sans limites.

## Bold Moves Executed
L'orchestrateur CEO a pris des décisions audacieuses pour dominer le marché.

## Market Domination Plan
Stratégie complète pour écraser la concurrence et devenir leader.

## Next Steps
1. Lever les fonds nécessaires (Series A+)
2. Exécuter le roadmap d'expansion agressif
3. Lancer les attaques concurrentielles planifiées
4. Préparer l'IPO à $1B+

## CEO Mindset
UNLIMITED AMBITION. TOTAL DOMINATION.
"""
            ceo_readme.write_text(ceo_content, encoding="utf-8")
        
        zipf.write(ceo_readme, "CEO_EMPIRE_README.md")
    
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=f"{run_id}_ceo_empire.zip"
    )
