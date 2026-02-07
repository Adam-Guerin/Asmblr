from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_THRESHOLD_PATH = BASE_DIR / "configs" / "thresholds.yaml"
DEFAULT_FEEDBACK_PATH = BASE_DIR / "data" / "product_feedback.jsonl"

SIGNAL_KEYS = (
    "market_size",
    "competition",
    "differentiation",
    "build_difficulty",
    "time_to_mvp",
    "traction_signals",
)
DEFAULT_WEIGHTS: dict[str, float] = {
    "market_size": 0.25,
    "competition": 0.20,
    "differentiation": 0.20,
    "build_difficulty": 0.15,
    "time_to_mvp": 0.10,
    "traction_signals": 0.10,
}


def _tokenize_text(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (value or "").lower()))


def _parse_keywords(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [part.strip().lower() for part in re.split(r"[,;\n]", raw) if part and part.strip()]
    else:
        items = [str(part).strip().lower() for part in raw if str(part).strip()]
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            cleaned.append(item)
            seen.add(item)
    return cleaned


def _compute_icp_alignment(
    *,
    idea: dict[str, Any] | None,
    topic: str,
    pain_statements: list[str] | None,
    icp_focus: str,
    icp_keywords: str | list[str] | None,
) -> float:
    if not icp_focus and not icp_keywords:
        return 0.0
    terms = _parse_keywords(icp_keywords)
    if icp_focus:
        terms.extend(_parse_keywords(icp_focus))
    term_tokens: set[str] = set()
    for term in terms:
        term_tokens.update(_tokenize_text(term))
    if not term_tokens:
        return 0.0

    text_parts = [topic or ""]
    if pain_statements:
        text_parts.extend(pain_statements)
    if idea:
        text_parts.extend(
            [
                str(idea.get("name", "")),
                str(idea.get("one_liner", "")),
                str(idea.get("target_user", "")),
                str(idea.get("problem", "")),
                str(idea.get("solution", "")),
                " ".join(idea.get("key_features", []) or []),
            ]
        )
    candidate_tokens = _tokenize_text(" ".join(text_parts))
    if not candidate_tokens:
        return 0.0
    overlap = len(candidate_tokens & term_tokens)
    return max(0.0, min(1.0, overlap / max(1, len(term_tokens))))


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None or not path.exists():
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _normalize_weights(weights: dict[str, Any]) -> dict[str, float]:
    data = {key: float(weights.get(key, DEFAULT_WEIGHTS[key])) for key in SIGNAL_KEYS}
    for key in SIGNAL_KEYS:
        data[key] = max(0.01, min(0.90, data[key]))
    total = sum(data.values())
    if total <= 0:
        return DEFAULT_WEIGHTS.copy()
    return {key: value / total for key, value in data.items()}


def detect_market_profile(topic: str = "", pain_statements: list[str] | None = None, idea: dict[str, Any] | None = None) -> str:
    text_parts = [topic or ""]
    if pain_statements:
        text_parts.extend(pain_statements)
    if idea:
        text_parts.extend(
            [
                str(idea.get("name", "")),
                str(idea.get("one_liner", "")),
                str(idea.get("target_user", "")),
                str(idea.get("problem", "")),
                str(idea.get("solution", "")),
                " ".join(idea.get("key_features", []) or []),
            ]
        )
    text = " ".join(text_parts).lower()

    creator_keywords = {
        "creator",
        "youtube",
        "tiktok",
        "instagram",
        "influencer",
        "newsletter",
        "audience",
        "content",
        "ugc",
    }
    local_keywords = {
        "restaurant",
        "clinic",
        "dentist",
        "salon",
        "local",
        "booking",
        "appointment",
        "shop",
        "retail",
        "neighborhood",
    }
    b2b_keywords = {
        "saas",
        "b2b",
        "workflow",
        "compliance",
        "crm",
        "erp",
        "sales",
        "support",
        "ops",
        "enterprise",
        "team",
    }

    tokens = set(re.findall(r"[a-z0-9]+", text))
    creator_hits = len(tokens & creator_keywords)
    local_hits = len(tokens & local_keywords)
    b2b_hits = len(tokens & b2b_keywords)

    if creator_hits > max(local_hits, b2b_hits):
        return "creator_tools"
    if local_hits > max(creator_hits, b2b_hits):
        return "local_services"
    if b2b_hits > 0:
        return "b2b_saas"
    return "default"


def _load_profile_weights(profile: str, threshold_path: Path | None = None) -> dict[str, float]:
    threshold_path = threshold_path or DEFAULT_THRESHOLD_PATH
    payload = _safe_load_yaml(threshold_path)
    profiles = payload.get("scoring_profiles") or {}
    if not isinstance(profiles, dict):
        profiles = {}

    # Backward compatibility with old thresholds.yaml (scoring_weights at root).
    root_weights = payload.get("scoring_weights") if isinstance(payload.get("scoring_weights"), dict) else {}
    base = _normalize_weights(root_weights or DEFAULT_WEIGHTS)
    selected = profiles.get(profile) if isinstance(profiles.get(profile), dict) else {}
    if profile != "default" and not selected:
        selected = profiles.get("default") if isinstance(profiles.get("default"), dict) else {}

    merged = dict(base)
    for key in SIGNAL_KEYS:
        if key in selected:
            try:
                merged[key] = float(selected[key])
            except Exception:
                continue
    return _normalize_weights(merged)


def _load_feedback_records(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or DEFAULT_FEEDBACK_PATH
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _calibrate_weights(
    profile_weights: dict[str, float],
    profile: str,
    feedback_path: Path | None = None,
    threshold_path: Path | None = None,
) -> tuple[dict[str, float], dict[str, Any]]:
    payload = _safe_load_yaml(threshold_path or DEFAULT_THRESHOLD_PATH)
    cfg = payload.get("scoring_calibration") if isinstance(payload.get("scoring_calibration"), dict) else {}
    enabled = bool(cfg.get("enabled", True))
    min_samples = int(cfg.get("min_samples", 3))
    max_shift = float(cfg.get("max_weight_shift", 0.06))
    max_shift = max(0.0, min(0.20, max_shift))
    if not enabled:
        return profile_weights, {"enabled": False, "applied": False, "reason": "disabled"}

    records = _load_feedback_records(feedback_path)
    profile_records: list[dict[str, Any]] = []
    for rec in records:
        topic = str(rec.get("topic", ""))
        if detect_market_profile(topic=topic) == profile:
            profile_records.append(rec)
    if len(profile_records) < min_samples:
        return profile_weights, {"enabled": True, "applied": False, "reason": "insufficient_samples", "samples": len(profile_records)}

    def _metric(name: str) -> float:
        values: list[float] = []
        for rec in profile_records:
            metrics = rec.get("metrics") or {}
            val = metrics.get(name)
            if isinstance(val, (int, float)):
                values.append(float(val))
        return sum(values) / len(values) if values else 0.0

    ctr = _metric("ctr_landing_pct")
    signup = _metric("signup_rate_pct")
    activation = _metric("activation_rate_pct")

    # Benchmarks aligned with product feedback scoring.
    ctr_delta = max(-1.0, min(1.0, (ctr - 2.0) / 2.0))
    signup_delta = max(-1.0, min(1.0, (signup - 8.0) / 8.0))
    activation_delta = max(-1.0, min(1.0, (activation - 25.0) / 25.0))

    shifts = {key: 0.0 for key in SIGNAL_KEYS}
    shifts["differentiation"] += 0.50 * ctr_delta
    shifts["traction_signals"] += 0.35 * ctr_delta + 0.35 * signup_delta
    shifts["market_size"] += 0.40 * signup_delta
    shifts["build_difficulty"] += 0.55 * (-activation_delta)
    shifts["time_to_mvp"] += 0.35 * (-activation_delta)
    shifts["competition"] += 0.15 * (-signup_delta)

    calibrated = dict(profile_weights)
    for key, raw_shift in shifts.items():
        delta = max(-max_shift, min(max_shift, raw_shift * max_shift))
        calibrated[key] = max(0.01, calibrated[key] + delta)
    calibrated = _normalize_weights(calibrated)
    return calibrated, {
        "enabled": True,
        "applied": True,
        "samples": len(profile_records),
        "avg_metrics": {
            "ctr_landing_pct": round(ctr, 3),
            "signup_rate_pct": round(signup, 3),
            "activation_rate_pct": round(activation, 3),
        },
    }


def heuristic_score(
    signals: dict[str, Any],
    *,
    topic: str = "",
    pain_statements: list[str] | None = None,
    idea: dict[str, Any] | None = None,
    market_profile: str | None = None,
    use_calibration: bool = True,
    threshold_path: Path | None = None,
    feedback_path: Path | None = None,
    icp_focus: str = "",
    icp_keywords: str | list[str] | None = None,
    icp_alignment_bonus_max: int = 0,
    return_meta: bool = False,
) -> int | tuple[int, dict[str, Any]]:
    market = float(signals.get("market_size", 50))
    competition = float(signals.get("competition", 50))
    differentiation = float(signals.get("differentiation", 50))
    build = float(signals.get("build_difficulty", 50))
    time = float(signals.get("time_to_mvp", 50))
    traction = float(signals.get("traction_signals", 50))

    profile = (market_profile or "").strip().lower() or detect_market_profile(
        topic=topic,
        pain_statements=pain_statements,
        idea=idea,
    )
    weights = _load_profile_weights(profile, threshold_path=threshold_path)
    calibration_meta = {"enabled": False, "applied": False, "reason": "disabled"}
    if use_calibration:
        weights, calibration_meta = _calibrate_weights(
            weights,
            profile=profile,
            feedback_path=feedback_path,
            threshold_path=threshold_path,
        )

    score = (
        market * weights["market_size"] +
        (100 - competition) * weights["competition"] +
        differentiation * weights["differentiation"] +
        (100 - build) * weights["build_difficulty"] +
        time * weights["time_to_mvp"] +
        traction * weights["traction_signals"]
    )
    icp_fit = _compute_icp_alignment(
        idea=idea,
        topic=topic,
        pain_statements=pain_statements,
        icp_focus=icp_focus,
        icp_keywords=icp_keywords,
    )
    capped_bonus = max(0, min(20, int(icp_alignment_bonus_max)))
    score += capped_bonus * ((2.0 * icp_fit) - 1.0)
    result = max(0, min(100, int(round(score))))
    if not return_meta:
        return result
    return result, {
        "market_profile": profile,
        "weights": {key: round(value, 6) for key, value in weights.items()},
        "calibration": calibration_meta,
        "icp_alignment": {
            "focus": icp_focus,
            "fit": round(icp_fit, 4),
            "bonus_max": capped_bonus,
        },
    }


def derive_signals(pain_statements: list[str]) -> dict[str, int]:
    text = " ".join(pain_statements).lower()
    market = 50 + 10 * text.count("team") + 5 * text.count("company")
    competition = 50 + 5 * text.count("existing") + 5 * text.count("already")
    differentiation = 50 + 5 * text.count("missing") + 5 * text.count("manual")
    build = 50 + 5 * text.count("integration") + 5 * text.count("compliance")
    time = 60 - 5 * text.count("complex")
    traction = 50 + 5 * text.count("need") + 5 * text.count("urgent")

    return {
        "market_size": max(10, min(90, market)),
        "competition": max(10, min(90, competition)),
        "differentiation": max(10, min(90, differentiation)),
        "build_difficulty": max(10, min(90, build)),
        "time_to_mvp": max(10, min(90, time)),
        "traction_signals": max(10, min(90, traction)),
    }
