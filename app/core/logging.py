from __future__ import annotations

import os
import sys
from contextvars import ContextVar
from typing import Any

from loguru import logger
from app.core.config import redact_value

_RUN_ID: ContextVar[str] = ContextVar("run_id", default="-")
_REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")


def set_log_context(run_id: str | None = None, request_id: str | None = None) -> None:
    if run_id is not None:
        _RUN_ID.set(run_id)
    if request_id is not None:
        _REQUEST_ID.set(request_id)


def clear_log_context() -> None:
    _RUN_ID.set("-")
    _REQUEST_ID.set("-")


def _patch_record(record: dict[str, Any]) -> None:
    record["extra"].setdefault("run_id", _RUN_ID.get())
    record["extra"].setdefault("request_id", _REQUEST_ID.get())
    record["message"] = str(redact_value(record.get("message", "")))
    redacted_extra: dict[str, Any] = {}
    for key, value in record["extra"].items():
        redacted_extra[key] = redact_value(value)
    record["extra"] = redacted_extra


def setup_logging() -> None:
    logger.remove()
    log_json = os.getenv("LOG_JSON", "false").lower() == "true"
    
    # Apply patching to logger before adding handlers
    logger.configure(patcher=_patch_record)
    
    if log_json:
        logger.add(
            sys.stdout,
            level="INFO",
            enqueue=True,
            backtrace=False,
            diagnose=False,
            serialize=True,
        )
    else:
        logger.add(
            sys.stdout,
            level="INFO",
            enqueue=True,
            backtrace=False,
            diagnose=False,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | run={extra[run_id]} req={extra[request_id]} | {message}",
        )

