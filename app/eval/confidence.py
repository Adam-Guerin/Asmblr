from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import Settings, get_settings


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _parse_embedded_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return {}


def _read_decision_status(run_dir: Path, override: Optional[str]) -> Optional[str]:
    if override:
        return override.upper()
    path = run_dir / "decision.md"
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if line.lower().startswith("- status:"):
            return line.split(":", 1)[1].strip().upper()
    return None


def _score_llm_health(run_dir: Path) -> Dict[str, Any]:
    path = run_dir / "llm_check.md"
    data = _parse_embedded_json(path)
    if not data:
        return {"score": 0, "details": "Missing or malformed llm_check.md", "reasons": ["Missing LLM self-test"]}
    text_ok = bool(data.get("text_ok"))
    json_ok = bool(data.get("json_ok"))
    score = int(round(10 * ((1 if text_ok else 0) + (1 if json_ok else 0)) / 2))
    reasons = []
    if not text_ok:
        reasons.append("Text prompt failed")
    if not json_ok:
        reasons.append("JSON prompt failed")
    details = "text_ok" if text_ok else ""
    if json_ok:
        details = (details + " + json_ok").strip()
    return {"score": score, "details": details or "LLM self-test issues", "reasons": reasons}


def _score_data_coverage(run_dir: Path, settings: Settings) -> Dict[str, Any]:
    path = run_dir / "data_check.md"
    data = _parse_embedded_json(path)
    pages = data.get("pages_count", 0)
    avg_len = data.get("avg_text_len", 0)
    unique_domains = data.get("unique_domains", 0)
    components: List[float] = []
    if settings.min_pages > 0:
        components.append(min(1.0, pages / max(1, settings.min_pages)))
    else:
        components.append(1.0)
    if settings.min_avg_text_len > 0:
        components.append(min(1.0, avg_len / max(1, settings.min_avg_text_len)))
    else:
        components.append(1.0)
    if settings.min_unique_domains > 0:
        components.append(min(1.0, unique_domains / max(1, settings.min_unique_domains)))
    else:
        components.append(1.0)
    market_score = 0.0
    market_path = run_dir / "market_signal_score.json"
    market_data = _read_json(market_path)
    if market_data:
        market_score = min(1.0, market_data.get("score", 0) / 100)
        components.append(market_score)
    ratio = sum(components) / len(components)
    score = int(round(25 * ratio))
    reasons: List[str] = []
    if ratio < 1:
        reasons.append("Data coverage below configured targets")
    if market_data and market_score < 0.5:
        reasons.append(f"Market signal low ({int(market_score * 100)}%)")
    details = f"pages={pages}, avg_len={avg_len}, domains={unique_domains}"
    return {"score": score, "details": details, "reasons": reasons}


def _score_pain_quality(run_dir: Path, settings: Settings) -> Dict[str, Any]:
    path = run_dir / "pains_validated.json"
    data = _read_json(path)
    validated = data.get("validated") or []
    ratio = 0.0
    if settings.min_pains > 0:
        ratio = min(1.0, len(validated) / max(1, settings.min_pains))
    else:
        ratio = 1.0 if validated else 0.0
    score = int(round(15 * ratio))
    reasons = []
    if not validated:
        reasons.append("No validated pain statements")
    elif ratio < 1.0:
        reasons.append("Fewer validated pains than configured")
    details = f"validated={len(validated)}"
    return {"score": score, "details": details, "reasons": reasons}


def _score_competitor_evidence(run_dir: Path, data_source: Dict[str, Any]) -> Dict[str, Any]:
    path = run_dir / "competitor_analysis.json"
    data = _read_json(path)
    comps = data.get("competitors") or data.get("items") or []
    score = 0
    reasons = []
    if comps:
        score = 15
    elif data_source.get("critical", {}).get("competitors") == "real":
        score = 10
        reasons.append("No detailed competitor analysis despite real competitors")
    else:
        reasons.append("Competitor evidence missing")
    return {"score": score, "details": f"entries={len(comps)}", "reasons": reasons}


def _score_traceability(run_dir: Path) -> Dict[str, Any]:
    path = run_dir / "opportunities.json"
    data = _read_json(path)
    items = data.get("items") or []
    if not items:
        return {"score": 0, "details": "No opportunities recorded", "reasons": ["Opportunities missing"]}
    valid = 0
    for item in items:
        idea = item.get("idea") or {}
        pain_ids = idea.get("pain_ids") or []
        sources = idea.get("sources") or []
        if pain_ids and sources:
            valid += 1
    ratio = valid / len(items)
    score = int(round(20 * ratio))
    reasons = []
    if ratio < 1:
        reasons.append("Some ideas missing pain_ids/sources")
    details = f"traceable={valid}/{len(items)}"
    return {"score": score, "details": details, "reasons": reasons}


def _score_artifact_integrity(run_dir: Path) -> Dict[str, Any]:
    files = [("prd.md", "PRD"), ("tech_spec.md", "Tech spec")]
    good = 0
    reasons = []
    for filename, label in files:
        path = run_dir / filename
        if not path.exists():
            reasons.append(f"{label} missing")
            continue
        text = path.read_text(encoding="utf-8").lower()
        if "fallback" in text:
            reasons.append(f"{label} contains fallback content")
            continue
        good += 1
    ratio = good / len(files)
    score = int(round(15 * ratio))
    details = f"{good}/{len(files)} artifacts clean"
    return {"score": score, "details": details, "reasons": reasons}


def compute_pre_artifact_confidence(
    run_dir: Path, settings: Settings | None = None
) -> Dict[str, Any]:
    settings = settings or get_settings()
    breakdown: Dict[str, Dict[str, Any]] = {}
    total = 0
    reasons: List[str] = []

    llm = _score_llm_health(run_dir)
    breakdown["llm_health"] = {"score": llm["score"], "max": 10, "details": llm["details"]}
    total += llm["score"]
    reasons.extend(llm["reasons"])

    data_cov = _score_data_coverage(run_dir, settings)
    breakdown["data_coverage"] = {"score": data_cov["score"], "max": 25, "details": data_cov["details"]}
    total += data_cov["score"]
    reasons.extend(data_cov["reasons"])

    pain_quality = _score_pain_quality(run_dir, settings)
    breakdown["pain_quality"] = {"score": pain_quality["score"], "max": 15, "details": pain_quality["details"]}
    total += pain_quality["score"]
    reasons.extend(pain_quality["reasons"])

    data_source = _read_json(run_dir / "data_source.json")
    competitor = _score_competitor_evidence(run_dir, data_source)
    breakdown["competitor_evidence"] = {
        "score": competitor["score"],
        "max": 15,
        "details": competitor["details"],
    }
    total += competitor["score"]
    reasons.extend(competitor["reasons"])

    traceability = _score_traceability(run_dir)
    breakdown["traceability"] = {"score": traceability["score"], "max": 20, "details": traceability["details"]}
    total += traceability["score"]
    reasons.extend(traceability["reasons"])

    unknown_fields = [
        key for key, value in (data_source.get("critical") or {}).items() if value == "unknown"
    ]
    if unknown_fields:
        reasons.append(f"Unknown critical sources: {', '.join(unknown_fields)}")

    return {"score": max(0, int(round(total))), "breakdown": breakdown, "reasons": list(dict.fromkeys(reasons))}


def compute_confidence(
    run_dir: Path, settings: Settings | None = None, status: Optional[str] = None
) -> Dict[str, Any]:
    settings = settings or get_settings()
    run_status = _read_decision_status(run_dir, status)
    reasons: List[str] = []
    caps: List[str] = []
    breakdown: Dict[str, Dict[str, Any]] = {}

    if run_status == "ABORT":
        reasons.append("Run aborted before completion")
        for key, max_points in (
            ("llm_health", 10),
            ("data_coverage", 25),
            ("pain_quality", 15),
            ("competitor_evidence", 15),
            ("traceability", 20),
            ("artifact_integrity", 15),
        ):
            breakdown[key] = {"score": 0, "max": max_points, "details": "run aborted"}
        payload = {
            "score": 0,
            "breakdown": breakdown,
            "reasons": reasons,
            "caps": caps,
        }
        (run_dir / "confidence.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    llm = _score_llm_health(run_dir)
    breakdown["llm_health"] = {"score": llm["score"], "max": 10, "details": llm["details"]}
    reasons.extend(llm["reasons"])

    data_source = _read_json(run_dir / "data_source.json")
    data_cov = _score_data_coverage(run_dir, settings)
    breakdown["data_coverage"] = {"score": data_cov["score"], "max": 25, "details": data_cov["details"]}
    reasons.extend(data_cov["reasons"])

    pain_quality = _score_pain_quality(run_dir, settings)
    breakdown["pain_quality"] = {"score": pain_quality["score"], "max": 15, "details": pain_quality["details"]}
    reasons.extend(pain_quality["reasons"])

    competitor = _score_competitor_evidence(run_dir, data_source)
    breakdown["competitor_evidence"] = {"score": competitor["score"], "max": 15, "details": competitor["details"]}
    reasons.extend(competitor["reasons"])

    traceability = _score_traceability(run_dir)
    breakdown["traceability"] = {"score": traceability["score"], "max": 20, "details": traceability["details"]}
    reasons.extend(traceability["reasons"])

    integrity = _score_artifact_integrity(run_dir)
    breakdown["artifact_integrity"] = {"score": integrity["score"], "max": 15, "details": integrity["details"]}
    reasons.extend(integrity["reasons"])

    total = sum(section["score"] for section in breakdown.values())

    critical = data_source.get("critical", {})
    unknown_fields = [key for key, value in critical.items() if value == "unknown"]
    if unknown_fields:
        reasons.append(f"Unknown data source for {', '.join(unknown_fields)}")
        total = max(0, total - 5 * len(unknown_fields))

    decision_flag = (data_source.get("decision") or "").lower()
    if decision_flag and decision_flag != "real":
        caps.append(f"Decision marked {decision_flag}")
        total = min(total, 25)

    payload = {
        "score": max(0, int(round(total))),
        "breakdown": breakdown,
        "reasons": reasons,
        "caps": caps,
    }
    (run_dir / "confidence.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
