from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path


def create_snapshot(data_dir: Path, runs_dir: Path, backup_root: Path | None = None) -> Path:
    backup_root = backup_root or (data_dir / "backups")
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"snapshot_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    db_path = data_dir / "app.db"
    if db_path.exists():
        shutil.copy2(db_path, backup_dir / "app.db")

    runs_archive = backup_dir / "runs.zip"
    if runs_dir.exists():
        shutil.make_archive(str(runs_archive.with_suffix("")), "zip", runs_dir)

    return backup_dir


def prune_backups(backup_root: Path, retention_days: int) -> int:
    if retention_days <= 0:
        return 0
    cutoff = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)
    removed = 0
    for entry in backup_root.iterdir():
        if not entry.is_dir() or not entry.name.startswith("snapshot_"):
            continue
        try:
            ts = entry.stat().st_mtime
        except Exception:
            continue
        if ts < cutoff:
            shutil.rmtree(entry, ignore_errors=True)
            removed += 1
    return removed
