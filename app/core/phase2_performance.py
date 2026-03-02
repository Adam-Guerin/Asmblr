from __future__ import annotations

import json
import time
from copy import deepcopy
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable


@dataclass(frozen=True)
class ModelProfile:
    model_name: str
    token_multiplier: float
    latency_multiplier: float
    confidence_delta: float


class DynamicModelSelector:
    """Phase 2 dynamic model selector based on uncertainty and stress profile."""

    def __init__(self) -> None:
        self._profiles: dict[str, ModelProfile] = {
            "fast": ModelProfile("qwen2.5-coder:7b", 0.78, 0.68, -0.02),
            "balanced": ModelProfile("llama3.1:8b", 0.95, 0.92, 0.00),
            "accurate": ModelProfile("llama3.1:70b", 1.18, 1.24, 0.04),
        }

    def select(self, uncertainty: str, stress_variant: str) -> ModelProfile:
        if uncertainty == "high" or stress_variant == "adversarial_corruption":
            return self._profiles["accurate"]
        if uncertainty == "low" and stress_variant == "base":
            return self._profiles["fast"]
        return self._profiles["balanced"]


class SmartCacheLayer:
    """Simple LRU + TTL cache for expensive run outputs."""

    def __init__(self, max_entries: int = 2048, ttl_seconds: int = 900) -> None:
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [key for key, (ts, _) in self._store.items() if now - ts > self.ttl_seconds]
        for key in expired:
            self._store.pop(key, None)

    def _evict_lru_if_needed(self) -> None:
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)

    def get(self, key: str) -> Any | None:
        self._evict_expired()
        if key not in self._store:
            self.misses += 1
            return None
        ts, value = self._store.pop(key)
        self._store[key] = (ts, value)
        self.hits += 1
        return deepcopy(value)

    def set(self, key: str, value: Any) -> None:
        self._evict_expired()
        self._store.pop(key, None)
        self._store[key] = (time.time(), deepcopy(value))
        self._evict_lru_if_needed()

    async def aget_or_set(self, key: str, producer: Callable[[], Awaitable[Any]]) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = await producer()
        self.set(key, value)
        return value

    def stats(self) -> dict[str, float]:
        total = self.hits + self.misses
        return {
            "entries": float(len(self._store)),
            "hits": float(self.hits),
            "misses": float(self.misses),
            "hit_rate": float(self.hits / total) if total else 0.0,
        }


class RealtimeMonitor:
    """Real-time monitoring sink for run-level events."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.output_dir / "realtime_events.jsonl"
        self.summary_file = self.output_dir / "realtime_summary.json"
        self._counters: dict[str, int] = defaultdict(int)
        self._totals: dict[str, float] = defaultdict(float)

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self._counters[event_type] += 1
        if "tokens_used" in payload:
            self._totals["tokens_used"] += float(payload["tokens_used"])
        if "latency" in payload:
            self._totals["latency"] += float(payload["latency"])

        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "payload": payload,
        }
        with self.events_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=True) + "\n")

    def flush_summary(self) -> None:
        total_events = int(sum(self._counters.values()))
        summary = {
            "total_events": total_events,
            "event_counts": dict(self._counters),
            "avg_tokens_used": (self._totals["tokens_used"] / total_events) if total_events else 0.0,
            "avg_latency": (self._totals["latency"] / total_events) if total_events else 0.0,
        }
        self.summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
