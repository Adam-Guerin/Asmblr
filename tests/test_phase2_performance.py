import asyncio
import json
import time
from pathlib import Path

from app.bench_edi import ArchitectureRunner
from app.core.phase2_performance import DynamicModelSelector, RealtimeMonitor, SmartCacheLayer


def test_dynamic_model_selector_uses_uncertainty_and_stress():
    selector = DynamicModelSelector()
    assert selector.select("high", "base").model_name == "llama3.1:70b"
    assert selector.select("medium", "adversarial_corruption").model_name == "llama3.1:70b"
    assert selector.select("low", "base").model_name == "qwen2.5-coder:7b"
    assert selector.select("medium", "base").model_name == "llama3.1:8b"


def test_smart_cache_layer_hit_and_ttl():
    cache = SmartCacheLayer(max_entries=4, ttl_seconds=1)
    cache.set("a", {"value": 1})
    assert cache.get("a") == {"value": 1}
    assert cache.stats()["hit_rate"] == 1.0
    time.sleep(1.1)
    assert cache.get("a") is None
    assert cache.stats()["misses"] >= 1.0


def test_realtime_monitor_writes_events_and_summary(tmp_path: Path):
    monitor = RealtimeMonitor(tmp_path / "rt")
    monitor.record_event("run_completed", {"tokens_used": 1200, "latency": 1.3})
    monitor.record_event("run_completed", {"tokens_used": 1000, "latency": 1.1})
    monitor.flush_summary()

    assert monitor.events_file.exists()
    assert monitor.summary_file.exists()
    summary = json.loads(monitor.summary_file.read_text(encoding="utf-8"))
    assert summary["total_events"] == 2
    assert summary["avg_tokens_used"] > 0
    assert summary["avg_latency"] > 0


def test_architecture_runner_phase2_applies_profile_and_cache(tmp_path: Path):
    contexts_dir = tmp_path / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": "ctx-1",
        "raw_text": "SaaS onboarding challenge",
        "timestamp": "2026-03-02T00:00:00",
        "source_url": "https://example.com",
        "industry_tag": "SaaS",
        "extracted_pains": ["onboarding friction"],
        "extracted_competitors": ["CompA"],
        "estimated_stage": "MVP",
        "geographic_cluster": "EU",
        "metadata": {"platform": "test"},
    }
    (contexts_dir / "context_0001.json").write_text(json.dumps(payload), encoding="utf-8")

    runner = ArchitectureRunner(str(contexts_dir), str(tmp_path / "runs"), phase2_performance=True)
    context = runner.contexts[0]
    result_1 = asyncio.run(runner.run_architecture("monolithic_baseline", context, seed=7, stress_variant="adversarial_corruption"))
    result_2 = asyncio.run(runner.run_architecture("monolithic_baseline", context, seed=7, stress_variant="adversarial_corruption"))

    assert "model_profile" in result_1
    assert result_1["model_profile"] == "llama3.1:70b"
    # second call should be served from cache and keep same values
    assert result_1["tokens_used"] == result_2["tokens_used"]
    assert result_1["latency"] == result_2["latency"]
    assert runner.cache_layer is not None
    assert runner.cache_layer.hits >= 1
