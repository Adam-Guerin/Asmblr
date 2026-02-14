from __future__ import annotations

import os
import sys
import re
import secrets
from contextvars import ContextVar
from typing import Any

from loguru import logger

# Enhanced redaction patterns for logging
_REDACTION_PATTERNS = {
    'api_key': re.compile(r'(api[_-]?key|token|secret)\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.IGNORECASE),
    'password': re.compile(r'(password|pwd|pass)\s*[:=]\s*["\']?([^\s"\']{6,})["\']?', re.IGNORECASE),
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'jwt': re.compile(r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*'),
    'bearer': re.compile(r'Bearer\s+([a-zA-Z0-9._-]+)', re.IGNORECASE),
}

_RUN_ID: ContextVar[str] = ContextVar("run_id", default="-")
_REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")


def enhanced_redact_value(value: Any) -> Any:
    """Enhanced data redaction for logging security"""
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            key_lower = str(key).lower()
            # Check for sensitive keys
            if any(pattern in key_lower for pattern in ['api_key', 'token', 'secret', 'password', 'pwd', 'key']):
                out[key] = _mask_sensitive(str(item))
            else:
                out[key] = enhanced_redact_value(item)
        return out
    
    if isinstance(value, list):
        return [enhanced_redact_value(item) for item in value]
    
    if isinstance(value, tuple):
        return tuple(enhanced_redact_value(item) for item in value)
    
    if isinstance(value, str):
        redacted = value
        # Apply all redaction patterns
        for pattern_name, pattern in _REDACTION_PATTERNS.items():
            def replacer(match):
                if pattern_name == 'email':
                    return match.group(0)[:2] + '*' * (len(match.group(0)) - 4) + match.group(0)[-2:]
                elif pattern_name in ['phone', 'credit_card', 'ssn']:
                    return '*' * (len(match.group(0)) - 4) + match.group(0)[-4:]
                elif pattern_name == 'bearer':
                    return 'Bearer ' + '*' * (len(match.group(1)) - 4) + match.group(1)[-4:]
                else:
                    # For API keys, tokens, JWTs
                    if len(match.group(0)) > 16:
                        return match.group(0)[:8] + '*' * (len(match.group(0)) - 12) + match.group(0)[-4:]
                    else:
                        return '*' * len(match.group(0))
            
            redacted = pattern.sub(replacer, redacted)
        return redacted
    
    return value


def _mask_sensitive(value: str) -> str:
    """Mask sensitive values"""
    if len(value) <= 8:
        return '*' * len(value)
    return value[:2] + '*' * (len(value) - 4) + value[-2:]

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
    record["message"] = str(enhanced_redact_value(record.get("message", "")))
    redacted_extra: dict[str, Any] = {}
    for key, value in record["extra"].items():
        redacted_extra[key] = enhanced_redact_value(value)
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

