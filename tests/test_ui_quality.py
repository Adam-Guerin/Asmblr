import json
from pathlib import Path

from app.ui_quality import aggregate_dashboard_metrics, load_run_metrics


def test_load_run_metrics_missing_files_safe(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "run_seed"
    run_dir.mkdir(parents=True)
    run_meta = {
        "id": "run_seed",
        "status": "aborted",
        "topic": "quality control",
        "created_at": "2026-01-25T10:00:00",
    }
    metrics = load_run_metrics(run_dir, run_meta)
    assert metrics["run_id"] == "run_seed"
    assert metrics["confidence_score"] is None
    assert "PRD" in metrics["missing_artifacts"]
    assert metrics["decision_status"] == "ABORTED"


def test_dashboard_aggregation_counts(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    run_complete = runs_dir / "run_complete"
    run_abort = runs_dir / "run_abort"
    run_complete.mkdir(parents=True)
    run_abort.mkdir(parents=True)

    confidence_payload = {"score": 82, "breakdown": {"llm_health": {"score": 10, "max": 10, "details": "ok"}}, "caps": [], "reasons": []}
    (run_complete / "confidence.json").write_text(json.dumps(confidence_payload), encoding="utf-8")
    market_payload = {"score": 70, "threshold": 40}
    (run_complete / "market_signal_score.json").write_text(json.dumps(market_payload), encoding="utf-8")
    (run_complete / "decision.md").write_text("- Status: PASS\n- Reason: good data\n", encoding="utf-8")

    (run_abort / "abort_reason.md").write_text("Insufficient market signal", encoding="utf-8")
    (run_abort / "decision.md").write_text("- Status: ABORT\n- Reason: market signal low\n", encoding="utf-8")
    (run_abort / "failure_report.json").write_text(
        json.dumps(
            {
                "status": "aborted",
                "last_stage": "crew_pipeline",
                "last_reason": "temporary provider issue",
                "stage_failures": [
                    {
                        "stage": "crew_pipeline",
                        "error_type": "TimeoutError",
                        "attempt": 2,
                        "max_attempts": 2,
                        "retryable": False,
                        "reason": "temporary provider issue",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    metrics = [
        load_run_metrics(
            run_complete,
            {
                "id": "run_complete",
                "status": "completed",
                "topic": "signal study",
                "created_at": "2026-01-25T12:00:00",
            },
        ),
        load_run_metrics(
            run_abort,
            {
                "id": "run_abort",
                "status": "aborted",
                "topic": "weak market",
                "created_at": "2026-01-25T13:00:00",
            },
        ),
    ]

    aggregated = aggregate_dashboard_metrics(metrics)
    assert aggregated["status_counts"]["completed"] == 1
    assert aggregated["status_counts"]["aborted"] == 1
    assert aggregated["avg_confidence"] == 82
    assert aggregated["runs_table"][0]["run_id"] == "run_abort"
    assert aggregated["top_abort_reasons"][0][0] == "Insufficient market signal"
    missing_names = [name for name, _ in aggregated["top_missing_artifacts"]]
    assert "PRD" in missing_names or "Tech spec" in missing_names
    abort_metrics = next(item for item in metrics if item["run_id"] == "run_abort")
    assert abort_metrics["failure_report"]["last_stage"] == "crew_pipeline"


def test_dashboard_business_kpis(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    run_complete = runs_dir / "run_complete"
    run_abort = runs_dir / "run_abort"
    run_kill = runs_dir / "run_kill"
    run_complete.mkdir(parents=True)
    run_abort.mkdir(parents=True)
    run_kill.mkdir(parents=True)

    (run_complete / "post_launch_metrics.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "ctr_landing_pct": 4.5,
                    "signup_rate_pct": 12.0,
                    "activation_rate_pct": 35.0,
                    "visitors": 200,
                    "signups": 24,
                    "activated_users": 8,
                }
            }
        ),
        encoding="utf-8",
    )

    metrics = [
        load_run_metrics(
            run_complete,
            {
                "id": "run_complete",
                "status": "completed",
                "topic": "launch analytics",
                "created_at": "2026-01-25T12:00:00",
                "updated_at": "2026-01-25T12:10:00",
            },
        ),
        load_run_metrics(
            run_abort,
            {
                "id": "run_abort",
                "status": "aborted",
                "topic": "weak signal",
                "created_at": "2026-01-25T12:00:00",
                "updated_at": "2026-01-25T12:05:00",
            },
        ),
        load_run_metrics(
            run_kill,
            {
                "id": "run_kill",
                "status": "killed",
                "topic": "bad economics",
                "created_at": "2026-01-25T12:00:00",
                "updated_at": "2026-01-25T12:08:00",
            },
        ),
    ]

    aggregated = aggregate_dashboard_metrics(metrics)
    assert aggregated["avg_mvp_ready_sec"] == 600.0
    assert aggregated["abort_rate_pct"] == 33.3
    assert aggregated["kill_rate_pct"] == 33.3
    assert aggregated["feedback_runs_count"] == 1
    assert aggregated["avg_signup_rate_pct"] == 12.0
    assert aggregated["avg_activation_rate_pct"] == 35.0
    assert aggregated["post_launch_signup_conversion_pct"] == 12.0
    assert aggregated["post_launch_activation_conversion_pct"] == 33.33
