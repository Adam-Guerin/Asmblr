import json
from pathlib import Path

from app.core.config import Settings
from app.eval.confidence import compute_confidence


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_basic_run(run_dir: Path, status: str, cap_decision: str | None = None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "decision.md").write_text(f"# Decision\n\n- Status: {status}\n- Reason: test run\n", encoding="utf-8")
    src = {
        "critical": {"pages": "unknown", "pains": "unknown", "competitors": "unknown", "seeds": "none"},
        "decision": cap_decision or "real",
    }
    _write_json(run_dir / "data_source.json", src)


def _populate_full_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "decision.md").write_text("# Decision\n\n- Status: PASS\n- Reason: rich data\n", encoding="utf-8")
    _write_json(
        run_dir / "data_source.json",
        {
            "critical": {"pages": "real", "pains": "real", "competitors": "real", "seeds": "none"},
            "decision": "real",
        },
    )
    (run_dir / "data_check.md").write_text("Data check: {\"pages_count\": 10, \"avg_text_len\": 400, \"unique_domains\": 4}", encoding="utf-8")
    _write_json(
        run_dir / "market_signal_score.json",
        {"score": 85, "sources_count": 6, "distinct_pains": 3, "repeat_score": 0.5, "unique_domains": 4, "threshold": 40},
    )
    _write_json(
        run_dir / "pains_validated.json",
        {
            "validated": [
                {"id": "pain_1", "text": "Operators struggle to manage vendors", "actor": "operators", "context": "when launching", "difficulty": "struggle"}
            ],
            "rejected": [],
        },
    )
    _write_json(
        run_dir / "competitor_analysis.json",
        {"competitors": [{"product_name": "Example", "url": "https://example.com", "pricing": "$0"}]},
    )
    _write_json(
        run_dir / "opportunities.json",
        {
            "items": [
                {
                    "idea": {
                        "name": "Signal Ops",
                        "pain_ids": ["pain_1"],
                        "sources": ["https://example.com/report"],
                        "hypotheses": ["Seed pain verified"],
                        "target_user": "Operators",
                        "problem": "Ops pain",
                        "solution": "Insight hub",
                        "key_features": [],
                    },
                    "score": {"name": "Signal Ops", "score": 85, "rationale": "strong", "risks": [], "signals": {}},
                }
            ]
        },
    )
    (run_dir / "llm_check.md").write_text("LLM check: {\"text_ok\": true, \"json_ok\": true}", encoding="utf-8")
    (run_dir / "prd.md").write_text("PRD content", encoding="utf-8")
    (run_dir / "tech_spec.md").write_text("Tech plan", encoding="utf-8")


def test_confidence_aborted_is_zero(tmp_path: Path) -> None:
    run_dir = tmp_path / "aborted"
    _write_basic_run(run_dir, "ABORT")
    result = compute_confidence(run_dir, settings=Settings(), status="ABORT")
    assert result["score"] == 0
    assert "Run aborted" in result["reasons"][0]


def test_confidence_caps_on_fallback_decision(tmp_path: Path) -> None:
    run_dir = tmp_path / "fallback"
    _populate_full_run(run_dir)
    _write_json(run_dir / "data_source.json", {"critical": {"pages": "real", "pains": "real", "competitors": "real", "seeds": "none"}, "decision": "fallback"})
    result = compute_confidence(run_dir, settings=Settings(), status="PASS")
    assert result["score"] <= 25
    assert any("fallback" in cap.lower() for cap in result["caps"])


def test_confidence_increases_with_real_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "good"
    _populate_full_run(run_dir)
    result = compute_confidence(run_dir, settings=Settings(), status="PASS")
    assert result["score"] >= 80
    assert (run_dir / "confidence.json").exists()
