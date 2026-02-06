"""Lightweight in-memory metrics registry for API/LLM monitoring."""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TimerSample:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def add(self, duration_ms: float) -> None:
        self.count += 1
        self.total_ms += duration_ms
        if duration_ms > self.max_ms:
            self.max_ms = duration_ms

    def snapshot(self) -> Dict[str, float]:
        avg = self.total_ms / self.count if self.count else 0.0
        return {"count": self.count, "avg_ms": round(avg, 2), "max_ms": round(self.max_ms, 2)}


class MetricsRegistry:
    """Thread-safe metrics aggregation for API requests and LLM calls."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._api_counts: Dict[str, int] = defaultdict(int)
        self._api_status: Dict[str, int] = defaultdict(int)
        self._api_timers: Dict[str, TimerSample] = defaultdict(TimerSample)
        self._llm_counts: Dict[str, int] = defaultdict(int)
        self._llm_failures: Dict[str, int] = defaultdict(int)
        self._llm_timers: Dict[str, TimerSample] = defaultdict(TimerSample)
        self._started_at = time.time()

    def record_api(self, path: str, status: int, duration_ms: float) -> None:
        key = path or "/"
        with self._lock:
            self._api_counts[key] += 1
            self._api_status[f"{key}:{status}"] += 1
            self._api_timers[key].add(duration_ms)

    def record_llm(self, model: str, duration_ms: float, ok: bool) -> None:
        key = model or "unknown"
        with self._lock:
            self._llm_counts[key] += 1
            if not ok:
                self._llm_failures[key] += 1
            self._llm_timers[key].add(duration_ms)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            api = {
                "counts": dict(self._api_counts),
                "status_counts": dict(self._api_status),
                "timers": {k: v.snapshot() for k, v in self._api_timers.items()},
            }
            llm = {
                "counts": dict(self._llm_counts),
                "failures": dict(self._llm_failures),
                "timers": {k: v.snapshot() for k, v in self._llm_timers.items()},
            }
        return {
            "uptime_s": round(time.time() - self._started_at, 2),
            "api": api,
            "llm": llm,
        }


METRICS = MetricsRegistry()
