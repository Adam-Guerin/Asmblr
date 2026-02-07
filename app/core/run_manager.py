import json
import os
import sqlite3
import time
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from collections.abc import Iterable
import httpx
import tempfile


class RunManager:
    def __init__(self, runs_dir: Path, data_dir: Path) -> None:
        self.runs_dir = runs_dir
        self.data_dir = data_dir
        self.db_path = data_dir / "app.db"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._last_maintenance_ts = 0.0
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    topic TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    output_dir TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)")
            conn.commit()

    def create_run(self, topic: str) -> str:
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        output_dir = self.runs_dir / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO runs (id, topic, status, created_at, updated_at, output_dir) VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, topic, "running", now, now, str(output_dir)),
            )
            conn.commit()
        return run_id

    def update_status(self, run_id: str, status: str) -> None:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE runs SET status=?, updated_at=? WHERE id=?",
                (status, now, run_id),
            )
            conn.commit()
        state = self.get_state(run_id)
        if state:
            self.update_state(run_id, status=status)
        if status in {"completed", "aborted", "killed", "failed"}:
            try:
                self.maybe_maintenance(min_interval_min=None)
            except Exception:
                pass

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT id, topic, status, created_at, updated_at, output_dir FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            return None
        keys = ["id", "topic", "status", "created_at", "updated_at", "output_dir"]
        return dict(zip(keys, row))

    def list_runs(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT id, topic, status, created_at, updated_at, output_dir FROM runs ORDER BY created_at DESC").fetchall()
        keys = ["id", "topic", "status", "created_at", "updated_at", "output_dir"]
        return [dict(zip(keys, row)) for row in rows]

    def write_artifact(self, run_id: str, relative_path: str, content: str) -> Path:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Run not found")
        output_dir = Path(run["output_dir"])
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def write_json(self, run_id: str, relative_path: str, payload: Any) -> Path:
        return self.write_artifact(run_id, relative_path, json.dumps(payload, indent=2))

    def write_json_atomic(self, run_id: str, relative_path: str, payload: Any) -> Path:
        """Write JSON file atomically to prevent race conditions."""
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Run not found")
        output_dir = Path(run["output_dir"])
        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file in the same directory to ensure atomic rename works
        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".tmp", 
            prefix=target.name + ".", 
            dir=target.parent
        )
        
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            
            # On Windows, we need to remove the target file first if it exists
            if target.exists():
                target.unlink()
            
            # Atomic rename
            os.rename(temp_path, target)
            
        except Exception:
            # Clean up temp file if something went wrong
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
            # Fallback to non-atomic write
            target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        
        return target

    def append_log(self, run_id: str, message: str) -> Path:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Run not found")
        output_dir = Path(run["output_dir"])
        log_path = output_dir / "progress.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().isoformat()
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {message}\n")
        webhook_url = self.get_webhook(run_id)
        if webhook_url:
            payload = {"run_id": run_id, "event": "progress", "timestamp": timestamp, "message": message}
            self._post_webhook(webhook_url, payload)
        return log_path

    def _state_path(self, run_id: str) -> Path:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Run not found")
        output_dir = Path(run["output_dir"])
        return output_dir / "run_state.json"

    def get_state(self, run_id: str) -> dict[str, Any] | None:
        try:
            path = self._state_path(run_id)
        except ValueError:
            return None
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def init_state(self, run_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        now = datetime.utcnow().isoformat()
        state = self.get_state(run_id) or {
            "run_id": run_id,
            "status": "running",
            "stage": "init",
            "completed": [],
            "attempts": {},
            "params": {},
            "created_at": now,
            "updated_at": now,
        }
        if params:
            state["params"] = params
        state["updated_at"] = now
        path = self._state_path(run_id)
        
        # Use atomic write for state file
        temp_path = path.with_suffix(".tmp")
        try:
            temp_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            # On Windows, we need to remove the target file first if it exists
            if path.exists():
                path.unlink()
            temp_path.rename(path)
        except Exception:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            # Fallback to non-atomic write
            path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        
        return state

    def update_state(self, run_id: str, **fields: Any) -> dict[str, Any]:
        state = self.get_state(run_id) or self.init_state(run_id)
        state.update(fields)
        state["updated_at"] = datetime.utcnow().isoformat()
        path = self._state_path(run_id)
        
        # Use atomic write for state file
        temp_path = path.with_suffix(".tmp")
        try:
            temp_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            # On Windows, we need to remove the target file first if it exists
            if path.exists():
                path.unlink()
            temp_path.rename(path)
        except Exception:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            # Fallback to non-atomic write
            path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        
        return state

    def begin_stage(self, run_id: str, stage: str) -> dict[str, Any]:
        state = self.get_state(run_id) or self.init_state(run_id)
        attempts = state.get("attempts") or {}
        attempts[stage] = int(attempts.get(stage, 0)) + 1
        state["attempts"] = attempts
        state["stage"] = stage
        return self.update_state(run_id, stage=stage, attempts=attempts)

    def complete_stage(self, run_id: str, stage: str) -> dict[str, Any]:
        state = self.get_state(run_id) or self.init_state(run_id)
        completed = list(state.get("completed") or [])
        if stage not in completed:
            completed.append(stage)
        return self.update_state(run_id, stage=stage, completed=completed)

    def set_webhook(self, run_id: str, url: str) -> Path:
        run = self.get_run(run_id)
        if not run:
            raise ValueError("Run not found")
        output_dir = Path(run["output_dir"])
        target = output_dir / "webhook.json"
        target.write_text(json.dumps({"url": url}, indent=2), encoding="utf-8")
        return target

    def get_webhook(self, run_id: str) -> str | None:
        run = self.get_run(run_id)
        if not run:
            return None
        output_dir = Path(run["output_dir"])
        target = output_dir / "webhook.json"
        if not target.exists():
            return None
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
            return payload.get("url")
        except Exception:
            return None

    def _post_webhook(self, url: str, payload: dict) -> None:
        try:
            timeout = httpx.Timeout(3.0, connect=2.0, read=3.0, write=3.0, pool=2.0)
            with httpx.Client(timeout=timeout) as client:
                client.post(url, json=payload)
        except Exception:
            return

    def maybe_maintenance(self, min_interval_min: int | None = 60) -> dict:
        if min_interval_min is None:
            min_interval_min = int(os.getenv("RUN_MAINTENANCE_INTERVAL_MIN", "60"))
        interval_s = max(1, int(min_interval_min)) * 60
        now = time.monotonic()
        if now - self._last_maintenance_ts < interval_s:
            return {"skipped": True, "reason": "interval"}
        self._last_maintenance_ts = now
        return self.run_maintenance()

    def run_maintenance(
        self,
        retention_days: int | None = 30,
        max_count: int | None = 200,
        compress_after_days: int | None = 7,
        archive_dirs: Iterable[str] | None = None,
    ) -> dict:
        if retention_days is None:
            retention_days = int(os.getenv("RUN_RETENTION_DAYS", "30"))
        if max_count is None:
            max_count = int(os.getenv("RUN_MAX_COUNT", "200"))
        if compress_after_days is None:
            compress_after_days = int(os.getenv("RUN_COMPRESS_AFTER_DAYS", "7"))
        if archive_dirs is None:
            archive_dirs = os.getenv(
                "RUN_ARCHIVE_DIRS",
                "repo_skeleton,landing_page,content_pack,mvp_repo,mvp_cycles,project_build",
            ).split(",")
        archive_dirs = [d for d in (archive_dirs or []) if d]
        if not archive_dirs:
            archive_dirs = []
        purged = self._purge_old_runs(retention_days=retention_days, max_count=max_count)
        compressed = self._compress_runs(compress_after_days=compress_after_days, archive_dirs=archive_dirs)
        return {"purged": purged, "compressed": compressed}

    def _purge_old_runs(self, retention_days: int, max_count: int) -> list[str]:
        runs = self.list_runs()
        if not runs:
            return []
        now = datetime.now(timezone.utc)
        keep: list[dict] = []
        purge: list[dict] = []
        for run in runs:
            status = run.get("status")
            if status not in {"completed", "aborted", "killed", "failed"}:
                keep.append(run)
                continue
            updated_at = run.get("updated_at") or run.get("created_at")
            try:
                ts = datetime.fromisoformat(updated_at)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = now
            age_days = (now - ts).days
            if retention_days > 0 and age_days >= retention_days:
                purge.append(run)
            else:
                keep.append(run)

        if max_count > 0 and len(keep) > max_count:
            overflow = sorted(keep, key=lambda r: r.get("updated_at") or "")[:-max_count]
            purge.extend([r for r in overflow if r.get("status") in {"completed", "aborted", "killed", "failed"}])

        purged_ids: list[str] = []
        for run in purge:
            run_id = run.get("id")
            output_dir = Path(run.get("output_dir") or "")
            if output_dir.exists():
                try:
                    shutil.rmtree(output_dir, ignore_errors=True)
                except Exception:
                    pass
            if run_id:
                self._delete_run_record(run_id)
                purged_ids.append(run_id)
        return purged_ids

    def _compress_runs(self, compress_after_days: int, archive_dirs: Iterable[str]) -> list[str]:
        if compress_after_days <= 0:
            return []
        archive_dirs = list(dict.fromkeys([d.strip() for d in archive_dirs if d and d.strip()]))
        runs = self.list_runs()
        now = datetime.now(timezone.utc)
        compressed: list[str] = []
        for run in runs:
            status = run.get("status")
            if status not in {"completed", "aborted", "killed", "failed"}:
                continue
            output_dir = Path(run.get("output_dir") or "")
            if not output_dir.exists() or not output_dir.is_dir():
                continue
            updated_at = run.get("updated_at") or run.get("created_at")
            try:
                ts = datetime.fromisoformat(updated_at)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = now
            age_days = (now - ts).days
            if age_days < compress_after_days:
                continue
            archive_path = output_dir / "archive.zip"
            if archive_path.exists():
                continue
            targets = [output_dir / d for d in archive_dirs if (output_dir / d).exists()]
            if not targets:
                continue
            try:
                with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for target in targets:
                        for file_path in target.rglob("*"):
                            if file_path.is_file():
                                arcname = file_path.relative_to(output_dir)
                                zf.write(file_path, arcname.as_posix())
                for target in targets:
                    for file_path in target.rglob("*"):
                        if file_path.is_file():
                            file_path.unlink(missing_ok=True)
                    for sub in sorted([p for p in target.rglob("*") if p.is_dir()], reverse=True):
                        try:
                            sub.rmdir()
                        except Exception:
                            pass
                    try:
                        target.rmdir()
                    except Exception:
                        pass
                compressed.append(run.get("id"))
            except Exception:
                try:
                    if archive_path.exists():
                        archive_path.unlink()
                except Exception:
                    pass
        return compressed

    def _delete_run_record(self, run_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM runs WHERE id=?", (run_id,))
            conn.commit()
