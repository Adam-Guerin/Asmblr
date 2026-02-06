"""Shared constants to avoid magic values across the codebase."""
from __future__ import annotations

from pathlib import Path

DEFAULT_CACHE_DIR = Path("data") / "cache"

WEB_MIN_TIMEOUT_S = 5
WEB_MAX_TIMEOUT_S = 60
WEB_CONNECT_TIMEOUT_S = 5.0
WEB_WRITE_TIMEOUT_S = 10.0
WEB_POOL_TIMEOUT_S = 5.0
WEB_USER_AGENT = "AI-Venture-Factory/1.0"
WEB_MAX_WORKERS = 4
WEB_RATE_MIN = 0.1
WEB_TOKEN_BUCKET_MULTIPLIER = 2.0
WEB_JITTER_MIN = 0.05
WEB_JITTER_MAX = 0.2

LLM_RETRY_ATTEMPTS = 3
LLM_RETRY_BASE_DELAY_S = 0.5
LLM_RETRY_JITTER_MAX_S = 0.2
