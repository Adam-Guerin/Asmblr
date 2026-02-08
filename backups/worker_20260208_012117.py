from __future__ import annotations

from rq import Connection, Worker
from redis import Redis
from fastapi import FastAPI, HTTPException
import threading
import time

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.llm import check_ollama


app = FastAPI(title="Asmblr Worker")


@app.get("/healthz")
def healthz():
    settings = get_settings()
    try:
        redis_conn = Redis.from_url(settings.redis_url)
        redis_conn.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Redis not ready: {exc}")
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    settings = get_settings()
    try:
        redis_conn = Redis.from_url(settings.redis_url)
        redis_conn.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Redis not ready: {exc}")
    try:
        check_ollama(settings.ollama_base_url, [settings.general_model, settings.code_model])
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama not ready: {exc}")
    return {"status": "ready"}


def _run_worker() -> None:
    settings = get_settings()
    redis_conn = Redis.from_url(settings.redis_url)
    with Connection(redis_conn):
        worker = Worker([settings.rq_queue_name])
        worker.work(with_scheduler=False)


def main() -> None:
    setup_logging()
    thread = threading.Thread(target=_run_worker, daemon=True)
    thread.start()
    try:
        import uvicorn

        settings = get_settings()
        uvicorn.run(app, host="0.0.0.0", port=settings.worker_port, log_level="info")
    except Exception:
        while thread.is_alive():
            time.sleep(0.5)


if __name__ == "__main__":
    main()
