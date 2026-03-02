import asyncio
import json
from pathlib import Path

from app.bench_edi import ArchitectureRunner
from app.core.phase3_scale import (
    AdvancedAnalyticsEngine,
    MarketplaceDeploymentManager,
    MultiTenantManager,
)


def test_multi_tenant_manager_builds_stable_tenant_ids():
    manager = MultiTenantManager()
    tenant_a = manager.resolve_tenant(industry_tag="SaaS", geography="EU")
    tenant_b = manager.resolve_tenant(industry_tag="SaaS", geography="EU")
    tenant_c = manager.resolve_tenant(industry_tag="Fintech", geography="US")

    assert tenant_a == tenant_b
    assert tenant_a != tenant_c
    assert tenant_a.startswith("tenant_")


def test_marketplace_deployment_manager_writes_manifest(tmp_path: Path):
    manager = MarketplaceDeploymentManager(tmp_path)
    manifest = manager.publish(
        run_id="run-001",
        architecture="a11_optimized",
        tenant_id="tenant_saas_eu",
        metrics={"final_edi": 0.12, "tokens_used": 2400},
    )

    path = tmp_path / "marketplace" / "run-001_manifest.json"
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["run_id"] == "run-001"
    assert loaded["deployment_channel"] == "marketplace"
    assert manifest["tenant_id"] == "tenant_saas_eu"


def test_advanced_analytics_engine_outputs_tenant_rollups(tmp_path: Path):
    engine = AdvancedAnalyticsEngine(tmp_path)
    records = [
        {"tenant_id": "tenant_a", "final_edi": 0.15, "tokens_used": 2500, "latency": 1.8},
        {"tenant_id": "tenant_a", "final_edi": 0.12, "tokens_used": 2300, "latency": 1.6},
        {"tenant_id": "tenant_b", "final_edi": 0.20, "tokens_used": 3000, "latency": 2.1},
    ]
    summary = engine.summarize(records)

    assert "tenant_a" in summary["tenants"]
    assert summary["tenants"]["tenant_a"]["runs"] == 2
    assert summary["global"]["runs"] == 3
    assert (tmp_path / "analytics" / "advanced_summary.json").exists()


def test_architecture_runner_phase3_scale_writes_tenant_artifacts(tmp_path: Path):
    contexts_dir = tmp_path / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": "ctx-1",
        "raw_text": "SaaS onboarding challenge and workflow fragmentation.",
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

    runner = ArchitectureRunner(
        str(contexts_dir),
        str(tmp_path / "runs"),
        phase2_performance=False,
        phase3_scale=True,
    )
    results = asyncio.run(runner.run_experiment("monolithic_baseline", k_seeds=1, stress_variants=["base"]))
    assert results
    tenant_id = results[0]["metadata"]["tenant_id"]
    run_id = results[0]["metadata"]["run_id"]

    tenant_run_dir = tmp_path / "runs" / "tenants" / tenant_id / run_id
    assert tenant_run_dir.exists()
    assert (tenant_run_dir / "decision.json").exists()
    assert (tmp_path / "runs" / "marketplace" / f"{run_id}_manifest.json").exists()
    assert (tmp_path / "runs" / "analytics" / "advanced_summary.json").exists()
