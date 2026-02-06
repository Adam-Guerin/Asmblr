import json
from pathlib import Path

from app.core.config import Settings
from app.core.models import Idea, IdeaScore
from app.core.pipeline import VenturePipeline


def _prepare_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    return settings


def test_record_product_feedback_persists_metrics(tmp_path):
    settings = _prepare_settings(tmp_path)
    pipeline = VenturePipeline(settings)
    run_id = pipeline.manager.create_run("compliance automation")

    payload = pipeline.record_product_feedback(
        run_id=run_id,
        ctr_landing=0.034,
        signup_rate=0.11,
        activation_rate=0.31,
        visitors=1200,
        signups=132,
        activated_users=41,
        window_days=14,
        notes="week 2 post-launch",
    )

    run_dir = settings.runs_dir / run_id
    metrics_path = run_dir / "post_launch_metrics.json"
    assert metrics_path.exists()
    saved = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert saved["metrics"]["ctr_landing_pct"] == 3.4
    assert saved["metrics"]["signup_rate_pct"] == 11.0
    assert saved["metrics"]["activation_rate_pct"] == 31.0
    assert payload["learning_score"] >= 60

    feedback_log = settings.data_dir / "product_feedback.jsonl"
    assert feedback_log.exists()
    lines = [line for line in feedback_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["run_id"] == run_id


def test_apply_learning_adjustment_prefers_matching_idea():
    settings = Settings()
    pipeline = VenturePipeline(settings)

    ideas = [
        Idea(
            name="Compliance Copilot",
            one_liner="Reduce audit workload",
            target_user="Ops teams",
            problem="Compliance reporting takes too long",
            solution="Automation and evidence collection",
            key_features=["audit", "compliance"],
            pain_ids=["p1"],
            sources=["https://example.com"],
            hypotheses=["Test demand from compliance teams"],
        ),
        Idea(
            name="Social Growth Bot",
            one_liner="Automate social posting",
            target_user="Creators",
            problem="Posting consistency is hard",
            solution="Scheduling assistant",
            key_features=["social", "growth"],
            pain_ids=["p2"],
            sources=["https://example.org"],
            hypotheses=["Creators need batching"],
        ),
    ]
    scores = [
        IdeaScore(name="Compliance Copilot", score=70, rationale="base", risks=[], signals={}),
        IdeaScore(name="Social Growth Bot", score=70, rationale="base", risks=[], signals={}),
    ]
    profile = {"score": 75, "confidence": 0.9, "adjustment": 6, "records": 3, "keywords": ["compliance", "audit"]}

    adjusted = pipeline._apply_product_learning_to_scores(scores, ideas, profile)
    first = next(item for item in adjusted if item.name == "Compliance Copilot")
    second = next(item for item in adjusted if item.name == "Social Growth Bot")
    assert first.score > second.score
    assert first.signals["product_learning_adjustment"] > second.signals["product_learning_adjustment"]
