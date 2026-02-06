from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict


@dataclass
class Bucket:
    tokens: float
    updated_at: float


class RateLimiter:
    def __init__(self, rate_per_minute: int, burst: int) -> None:
        self.rate_per_minute = max(0, int(rate_per_minute))
        self.burst = max(1, int(burst))
        self._lock = Lock()
        self._buckets: Dict[str, Bucket] = {}

    def allow(self, key: str) -> bool:
        if self.rate_per_minute <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = Bucket(tokens=float(self.burst), updated_at=now)
                self._buckets[key] = bucket
            elapsed = now - bucket.updated_at
            refill = (elapsed / 60.0) * self.rate_per_minute
            bucket.tokens = min(float(self.burst), bucket.tokens + refill)
            bucket.updated_at = now
            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True
            return False
