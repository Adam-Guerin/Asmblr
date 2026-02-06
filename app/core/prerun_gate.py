from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PreRunGateResult:
    ok: bool
    reasons: List[str]


class PreRunGate:
    def __init__(
        self,
        min_pages: int,
        min_pains: int,
        min_competitors: int,
        min_signal_quality: int = 0,
    ) -> None:
        self.min_pages = min_pages
        self.min_pains = min_pains
        self.min_competitors = min_competitors
        self.min_signal_quality = min_signal_quality

    def evaluate(
        self,
        pages: List[Dict[str, Any]],
        pains: List[str],
        competitors: List[Dict[str, Any]],
        icp: str,
        data_source: Dict[str, str],
        signal_quality: Dict[str, Any] | None = None,
    ) -> PreRunGateResult:
        reasons: List[str] = []

        if data_source.get("pages") == "fallback":
            reasons.append("pages are fallback")
        if len(pages) < self.min_pages:
            reasons.append(f"pages < {self.min_pages}")

        if data_source.get("pains") == "fallback":
            reasons.append("pain_statements are fallback")
        if len(pains) < self.min_pains:
            reasons.append(f"pain_statements < {self.min_pains}")

        if data_source.get("competitors") == "fallback":
            reasons.append("competitors are fallback")
        if len([c for c in competitors if c.get("product_name") not in (None, "unknown")]) < self.min_competitors:
            reasons.append(f"competitors < {self.min_competitors}")

        if not icp or icp.lower().strip() == "unknown":
            reasons.append("ICP missing")

        # Explicit hard gate: no fallback allowed for critical inputs.
        critical = ("pages", "pains", "competitors")
        if any(data_source.get(key) == "fallback" for key in critical):
            reasons.append("critical data source fallback detected")

        if signal_quality and signal_quality.get("score", 0) < self.min_signal_quality:
            reasons.append(
                f"signal quality {signal_quality.get('score', 0)} below threshold {self.min_signal_quality}"
            )

        return PreRunGateResult(ok=len(reasons) == 0, reasons=reasons)
