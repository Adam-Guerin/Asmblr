import json
from pathlib import Path

from app.core.scoring import heuristic_score, derive_signals, detect_market_profile


def test_heuristic_score_range():
    signals = derive_signals(["team needs help", "manual process is hard"]) 
    score = heuristic_score(signals)
    assert 0 <= score <= 100


def test_detect_market_profile_keywords():
    assert detect_market_profile(topic="B2B SaaS compliance ops tool") == "b2b_saas"
    assert detect_market_profile(topic="Creator growth toolkit for YouTube") == "creator_tools"
    assert detect_market_profile(topic="Booking automation for local salons") == "local_services"


def test_heuristic_score_changes_by_profile():
    signals = {
        "market_size": 70,
        "competition": 40,
        "differentiation": 80,
        "build_difficulty": 30,
        "time_to_mvp": 65,
        "traction_signals": 72,
    }
    b2b = heuristic_score(signals, market_profile="b2b_saas", use_calibration=False)
    creator = heuristic_score(signals, market_profile="creator_tools", use_calibration=False)
    local = heuristic_score(signals, market_profile="local_services", use_calibration=False)
    assert len({b2b, creator, local}) >= 2


def test_heuristic_score_calibration_from_feedback(tmp_path: Path):
    feedback_path = tmp_path / "product_feedback.jsonl"
    records = [
        {
            "topic": "creator growth tool",
            "metrics": {"ctr_landing_pct": 5.0, "signup_rate_pct": 14.0, "activation_rate_pct": 35.0},
            "learning_score": 80,
            "confidence": 0.8,
        },
        {
            "topic": "creator newsletter analytics",
            "metrics": {"ctr_landing_pct": 6.2, "signup_rate_pct": 12.5, "activation_rate_pct": 32.0},
            "learning_score": 78,
            "confidence": 0.7,
        },
        {
            "topic": "creator content ops",
            "metrics": {"ctr_landing_pct": 4.8, "signup_rate_pct": 11.0, "activation_rate_pct": 30.0},
            "learning_score": 74,
            "confidence": 0.75,
        },
    ]
    feedback_path.write_text("\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8")

    signals = derive_signals(["Creators need better onboarding and recurring engagement."])
    no_calib = heuristic_score(
        signals,
        market_profile="creator_tools",
        use_calibration=False,
    )
    with_calib, meta = heuristic_score(
        signals,
        market_profile="creator_tools",
        use_calibration=True,
        feedback_path=feedback_path,
        return_meta=True,
    )
    assert meta["calibration"]["applied"] is True
    assert 0 <= no_calib <= 100
    assert 0 <= with_calib <= 100


def test_heuristic_score_icp_alignment_bonus():
    signals = {
        "market_size": 65,
        "competition": 45,
        "differentiation": 60,
        "build_difficulty": 45,
        "time_to_mvp": 70,
        "traction_signals": 60,
    }
    aligned_idea = {
        "name": "Founder Pipeline Ops",
        "target_user": "B2B SaaS founders",
        "problem": "Pre-seed teams struggle to validate quickly",
        "solution": "Lean validation workflow",
        "key_features": ["startup experiments"],
    }
    off_idea = {
        "name": "Local Salon Booking",
        "target_user": "Neighborhood salons",
        "problem": "Appointment scheduling friction",
        "solution": "Booking assistant",
        "key_features": ["calendar sync"],
    }
    common_kwargs = {
        "topic": "Founders B2B SaaS pre-seed",
        "icp_focus": "Founders B2B SaaS pre-seed",
        "icp_keywords": "founder,b2b,saas,pre-seed,startup",
        "icp_alignment_bonus_max": 8,
        "use_calibration": False,
    }
    aligned = heuristic_score(signals, idea=aligned_idea, **common_kwargs)
    off = heuristic_score(signals, idea=off_idea, **common_kwargs)
    assert aligned > off
