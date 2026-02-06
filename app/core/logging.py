from __future__ import annotations

import os
import sys
from contextvars import ContextVar
from typing import Any, Dict

from loguru import logger

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


def _patch_record(record: Dict[str, Any]) -> None:
    record["extra"].setdefault("run_id", _RUN_ID.get())
    record["extra"].setdefault("request_id", _REQUEST_ID.get())


def setup_logging() -> None:
    logger.remove()
    log_json = os.getenv("LOG_JSON", "false").lower() == "true"
    if log_json:
        logger.add(
            sys.stdout,
            level="INFO",
            enqueue=True,
            backtrace=False,
            diagnose=False,
            serialize=True,
            patcher=_patch_record,
        )
    else:
        logger.add(
            sys.stdout,
            level="INFO",
            enqueue=True,
            backtrace=False,
            diagnose=False,
            patcher=_patch_record,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | run={extra[run_id]} req={extra[request_id]} | {message}",
        )

