# Operations (Asmblr)

This document covers day-2 operations for the Asmblr application itself (API/UI/worker),
not the generated MVP repos.

## Services
- API: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- UI: `streamlit run app/ui.py --server.address 127.0.0.1 --server.port 8501`
- Worker (RQ): `python -m app.worker`
- Redis: `redis-server` or `docker compose up`

## Crash Playbooks

### API crashes or hangs
1. Check readiness:
   - `GET /healthz`
   - `GET /readyz`
2. Inspect logs:
   - app logs (stdout)
   - `data/audit.log` for run lifecycle
3. Confirm Ollama:
   - `GET http://localhost:11434/api/tags`
4. Restart API:
   - `uvicorn app.main:app --host 127.0.0.1 --port 8000`

### Worker crashes or stops processing
1. Check worker health:
   - `GET http://localhost:8001/healthz`
   - `GET http://localhost:8001/readyz`
2. Check Redis:
   - `redis-cli ping`
3. Inspect queue:
   - `python -m rq info -u $REDIS_URL`
4. Restart worker:
   - `python -m app.worker`

### UI crashes or blank page
1. Inspect Streamlit logs.
2. Verify API health.
3. Restart UI:
   - `streamlit run app/ui.py --server.address 127.0.0.1 --server.port 8501`

## Backup & Restore

### Backup
```bash
python -m app backup
```
Creates a snapshot of `data/app.db` and `runs/` (zipped) in `data/backups/`.

### Restore
1. Stop API/UI/worker.
2. Unzip the latest snapshot.
3. Restore `data/app.db` into `data/`.
4. Restore `runs/` directory.
5. Start services.

## Updates

### Code update
1. Pull changes:
   - `git pull`
2. Rebuild dependencies:
   - `pip install -r requirements.txt`
3. Restart services.

### Docker Compose update
```bash
docker compose pull
docker compose up --build
```

## Routine Checks
- API metrics: `GET /metrics` and `/metrics/prometheus`
- Worker health: `GET http://localhost:8001/healthz`
- Queue status: `GET /run/{run_id}/job`
- Storage: `runs/` retention + `python -m app cleanup`

## Self-healing Mode

The pipeline supports stage-level self-healing for transient errors.

- Enable/disable: `ENABLE_SELF_HEALING=true|false`
- Stage retries: `STAGE_RETRY_ATTEMPTS` (default `2`)
- Retry backoff (seconds): `STAGE_RETRY_BACKOFF_SEC` (default `1.0`)
- Fallback models:
  - `GENERAL_MODEL_FALLBACKS` (comma-separated)
  - `CODE_MODEL_FALLBACKS` (comma-separated)

Per-run diagnostics:
- `runs/<run_id>/llm_model_selection.json` (active/fallback model pair)
- `runs/<run_id>/failure_report.json` (standardized failures by stage)
- `runs/<run_id>/failure_report.md` (human-readable summary)
