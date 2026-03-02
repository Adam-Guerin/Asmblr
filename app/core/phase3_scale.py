from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    industry_tag: str
    geography: str


class MultiTenantManager:
    """Resolve tenant identity and filesystem layout for tenant isolation."""

    def resolve_tenant(self, industry_tag: str, geography: str) -> str:
        industry = (industry_tag or "unknown").strip().lower()
        geo = (geography or "global").strip().lower()
        digest = hashlib.md5(f"{industry}:{geo}".encode("utf-8")).hexdigest()[:8]
        return f"tenant_{digest}"

    def tenant_run_dir(self, output_dir: str | Path, tenant_id: str, run_id: str) -> Path:
        path = Path(output_dir) / "tenants" / tenant_id / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path


class MarketplaceDeploymentManager:
    """Publish benchmark run metadata to a marketplace-ready manifest."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.marketplace_dir = self.output_dir / "marketplace"
        self.marketplace_dir.mkdir(parents=True, exist_ok=True)

    def publish(
        self,
        run_id: str,
        architecture: str,
        tenant_id: str,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        manifest = {
            "run_id": run_id,
            "architecture": architecture,
            "tenant_id": tenant_id,
            "deployment_channel": "marketplace",
            "published_at": time.time(),
            "metrics": metrics,
        }
        path = self.marketplace_dir / f"{run_id}_manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest


class AdvancedAnalyticsEngine:
    """Compute tenant-aware analytics rollups."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.analytics_dir = self.output_dir / "analytics"
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        self.summary_file = self.analytics_dir / "advanced_summary.json"

    def summarize(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        tenant_rollups: dict[str, dict[str, float]] = {}
        for rec in records:
            tenant = rec.get("tenant_id", "tenant_unknown")
            roll = tenant_rollups.setdefault(
                tenant,
                {"runs": 0.0, "edi_total": 0.0, "tokens_total": 0.0, "latency_total": 0.0},
            )
            roll["runs"] += 1.0
            roll["edi_total"] += float(rec.get("final_edi", 0.0))
            roll["tokens_total"] += float(rec.get("tokens_used", 0.0))
            roll["latency_total"] += float(rec.get("latency", 0.0))

        tenants_out: dict[str, dict[str, float]] = {}
        global_runs = 0.0
        global_edi = 0.0
        global_tokens = 0.0
        global_latency = 0.0

        for tenant, roll in tenant_rollups.items():
            runs = max(1.0, roll["runs"])
            tenants_out[tenant] = {
                "runs": int(roll["runs"]),
                "mean_final_edi": roll["edi_total"] / runs,
                "mean_tokens_used": roll["tokens_total"] / runs,
                "mean_latency": roll["latency_total"] / runs,
            }
            global_runs += roll["runs"]
            global_edi += roll["edi_total"]
            global_tokens += roll["tokens_total"]
            global_latency += roll["latency_total"]

        global_den = max(1.0, global_runs)
        summary = {
            "tenants": tenants_out,
            "global": {
                "runs": int(global_runs),
                "mean_final_edi": global_edi / global_den,
                "mean_tokens_used": global_tokens / global_den,
                "mean_latency": global_latency / global_den,
            },
        }
        self.summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary
