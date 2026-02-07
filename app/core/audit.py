from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.core.config import redact_value


def write_audit_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload = redact_value(payload)
    payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    line = json.dumps(payload, ensure_ascii=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
