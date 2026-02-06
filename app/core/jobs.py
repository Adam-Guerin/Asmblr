from __future__ import annotations

from typing import Optional
from pathlib import Path

from datetime import timedelta

from redis import Redis
from rq import Queue
from rq.job import Job

from app.core.config import get_settings
from app.core.models import SeedInputs
from app.core.run_manager import RunManager


def _queue() -> Queue:
    settings = get_settings()
    redis_conn = Redis.from_url(settings.redis_url)
    return Queue(settings.rq_queue_name, connection=redis_conn, default_timeout=settings.rq_default_timeout)


def enqueue_run(
    run_id: str,
    topic: str,
    n_ideas: int,
    fast: bool,
    seeds: SeedInputs,
    webhook_url: Optional[str],
    deploy: bool = False,
    deploy_dry_run: bool = True,
) -> str:
    q = _queue()
    job = q.enqueue(
        "app.core.jobs.run_job",
        run_id=run_id,
        topic=topic,
        n_ideas=n_ideas,
        fast=fast,
        seed_payload={
            "icp": seeds.icp,
            "pains": list(seeds.pains),
            "competitors": list(seeds.competitors),
            "context": seeds.context,
            "theme": seeds.theme,
        },
        webhook_url=webhook_url,
        deploy=deploy,
        deploy_dry_run=deploy_dry_run,
    )
    RunManager(get_settings().runs_dir, get_settings().data_dir).update_state(run_id, job_id=job.id)
    return job.id


def enqueue_resume(run_id: str) -> str:
    q = _queue()
    job = q.enqueue("app.core.jobs.resume_job", run_id=run_id)
    RunManager(get_settings().runs_dir, get_settings().data_dir).update_state(run_id, job_id=job.id)
    return job.id


def get_job_status(run_id: str) -> dict:
    settings = get_settings()
    manager = RunManager(settings.runs_dir, settings.data_dir)
    state = manager.get_state(run_id) or {}
    job_id = state.get("job_id")
    if not job_id:
        return {"status": "unknown", "job_id": None}
    try:
        redis_conn = Redis.from_url(settings.redis_url)
        job = Job.fetch(job_id, connection=redis_conn)
        status = job.get_status()
        position = None
        total = None
        if status == "queued":
            q = Queue(settings.rq_queue_name, connection=redis_conn)
            try:
                position = q.get_job_position(job)
                total = len(q)
            except Exception:
                position = None
        return {
            "status": status,
            "job_id": job_id,
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "position": position,
            "queue_total": total,
        }
    except Exception:
        return {"status": "unknown", "job_id": job_id}


def run_job(
    run_id: str,
    topic: str,
    n_ideas: int,
    fast: bool,
    seed_payload: dict,
    webhook_url: Optional[str],
    deploy: bool = False,
    deploy_dry_run: bool = True,
) -> None:
    from app.core.logging import set_log_context, clear_log_context
    from app.core.pipeline import VenturePipeline
    from app.core.models import SeedInputs
    from app.core.config import get_settings
    from app.core.run_manager import RunManager
    from loguru import logger
    from app.core.audit import write_audit_event

    settings = get_settings()
    if deploy:
        settings.enable_deploy = True
        settings.deploy_dry_run = bool(deploy_dry_run)
    manager = RunManager(settings.runs_dir, settings.data_dir)
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_started",
            "run_id": run_id,
            "job_id": manager.get_state(run_id).get("job_id") if manager.get_state(run_id) else None,
            "actor": "worker",
        },
    )
    if settings.run_max_concurrent > 0:
        running = [r for r in manager.list_runs() if r.get("status") == "running"]
        if len(running) >= settings.run_max_concurrent:
            logger.warning(
                "Run {run_id} deferred due to concurrency limit ({limit})",
                run_id=run_id,
                limit=settings.run_max_concurrent,
            )
            q = _queue()
            q.enqueue_in(
                timedelta(seconds=settings.run_queue_backoff_sec),
                "app.core.jobs.run_job",
                run_id=run_id,
                topic=topic,
                n_ideas=n_ideas,
                fast=fast,
                seed_payload=seed_payload,
                webhook_url=webhook_url,
            )
            manager.update_status(run_id, "queued")
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "run_deferred",
                    "run_id": run_id,
                    "job_id": manager.get_state(run_id).get("job_id") if manager.get_state(run_id) else None,
                    "actor": "worker",
                },
            )
            return
    set_log_context(run_id=run_id)
    try:
        pipeline = VenturePipeline(settings)
        seeds = SeedInputs(
            icp=seed_payload.get("icp"),
            pains=list(seed_payload.get("pains") or []),
            competitors=list(seed_payload.get("competitors") or []),
            context=seed_payload.get("context"),
            theme=seed_payload.get("theme"),
        )
        try:
            pipeline.run(topic, n_ideas, fast, run_id, seed_inputs=seeds)
        finally:
            run_info = RunManager(settings.runs_dir, settings.data_dir).get_run(run_id) or {}
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "run_finished",
                    "run_id": run_id,
                    "job_id": manager.get_state(run_id).get("job_id") if manager.get_state(run_id) else None,
                    "final_status": run_info.get("status"),
                    "actor": "worker",
                },
            )
        if webhook_url:
            def _notify_webhook(url: str, payload: dict) -> None:
                try:
                    import httpx

                    timeout = httpx.Timeout(5.0, connect=3.0, read=5.0, write=5.0, pool=3.0)
                    with httpx.Client(timeout=timeout) as client:
                        client.post(url, json=payload)
                except Exception:
                    return

            run = RunManager(settings.runs_dir, settings.data_dir).get_run(run_id) or {}
            payload = {
                "run_id": run_id,
                "status": run.get("status"),
                "output_dir": run.get("output_dir"),
            }
            _notify_webhook(webhook_url, payload)
    finally:
        clear_log_context()


def resume_job(run_id: str) -> None:
    from app.core.logging import set_log_context, clear_log_context
    from app.core.pipeline import VenturePipeline
    from app.core.config import get_settings
    from app.core.audit import write_audit_event
    from app.core.run_manager import RunManager

    settings = get_settings()
    manager = RunManager(settings.runs_dir, settings.data_dir)
    write_audit_event(
        Path(settings.audit_log_file),
        {
            "event": "run_resume_started",
            "run_id": run_id,
            "job_id": manager.get_state(run_id).get("job_id") if manager.get_state(run_id) else None,
            "actor": "worker",
        },
    )
    set_log_context(run_id=run_id)
    try:
        pipeline = VenturePipeline(settings)
        run = pipeline.manager.get_run(run_id)
        if not run:
            return
        try:
            pipeline.run(run["topic"], settings.default_n_ideas, fast_mode=settings.fast_mode, run_id=run_id, resume=True)
        finally:
            run_info = manager.get_run(run_id) or {}
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "run_resume_finished",
                    "run_id": run_id,
                    "job_id": manager.get_state(run_id).get("job_id") if manager.get_state(run_id) else None,
                    "final_status": run_info.get("status"),
                    "actor": "worker",
                },
            )
    finally:
        clear_log_context()
