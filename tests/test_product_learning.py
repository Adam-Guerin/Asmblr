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


def test_adaptive_thresholds_relax_for_strong_segment(tmp_path):
    settings = _prepare_settings(tmp_path)
    settings.signal_quality_threshold = 45
    settings.kill_threshold = 55
    pipeline = VenturePipeline(settings)

    feedback_path = settings.data_dir / "product_feedback.jsonl"
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "topic": "AI compliance automation for audit teams",
            "learning_score": 82,
            "confidence": 0.9,
        },
        {
            "topic": "Compliance audit copilot for SMB teams",
            "learning_score": 77,
            "confidence": 0.85,
        },
        {
            "topic": "Customer support chatbot",
            "learning_score": 42,
            "confidence": 0.6,
        },
    ]
    feedback_path.write_text("\n".join(json.dumps(item) for item in rows) + "\n", encoding="utf-8")

    adapted = pipeline._compute_adaptive_thresholds("Compliance automation for audit workflows")
    assert adapted["segment_records"] >= 2
    assert adapted["signal_quality_threshold"] <= 45
    assert adapted["kill_threshold"] <= 55
    assert "auto-adjusted" in adapted["notes"].lower()


def test_adaptive_thresholds_keep_base_when_segment_evidence_is_thin(tmp_path):
    settings = _prepare_settings(tmp_path)
    settings.signal_quality_threshold = 45
    settings.kill_threshold = 55
    pipeline = VenturePipeline(settings)

    feedback_path = settings.data_dir / "product_feedback.jsonl"
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "topic": "AI compliance automation for audit teams",
            "learning_score": 35,
            "confidence": 0.8,
        }
    ]
    feedback_path.write_text("\n".join(json.dumps(item) for item in rows) + "\n", encoding="utf-8")

    adapted = pipeline._compute_adaptive_thresholds("Compliance automation for audit workflows")
    assert adapted["segment_records"] == 1
    assert adapted["signal_quality_threshold"] == 45
    assert adapted["kill_threshold"] == 55


def test_historical_learning_penalizes_repeated_failure_pattern(tmp_path):
    settings = _prepare_settings(tmp_path)
    settings.learning_exploration_rate = 0.0
    pipeline = VenturePipeline(settings)

    feedback_path = settings.data_dir / "product_feedback.jsonl"
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {"topic": "Compliance automation assistant", "learning_score": 82, "confidence": 0.9},
        {"topic": "Creator social scheduling bot", "learning_score": 32, "confidence": 0.85},
    ]
    feedback_path.write_text("\n".join(json.dumps(item) for item in rows) + "\n", encoding="utf-8")

    failed_run_id = pipeline.manager.create_run("creator content bot")
    pipeline.manager.write_artifact(failed_run_id, "abort_reason.md", "Weak retention and low activation from creator segment")
    pipeline.manager.update_status(failed_run_id, "aborted")

    ideas = [
        Idea(
            name="Compliance Copilot",
            one_liner="Help audit teams",
            target_user="Ops",
            problem="Audit work is slow",
            solution="Automate compliance evidence",
            key_features=["compliance", "audit"],
        ),
        Idea(
            name="Creator Bot",
            one_liner="Schedule creator posts",
            target_user="Creators",
            problem="Content posting is hard",
            solution="Automate social scheduling",
            key_features=["creator", "social", "scheduling"],
        ),
    ]
    scores = [
        IdeaScore(name="Compliance Copilot", score=70, rationale="base", risks=[], signals={}),
        IdeaScore(name="Creator Bot", score=70, rationale="base", risks=[], signals={}),
    ]

    memory = pipeline._build_historical_learning_memory("automation assistant", run_id="new_run")
    adjusted = pipeline._apply_historical_learning_to_scores(
        scores=scores,
        ideas=ideas,
        topic="automation assistant",
        run_id="new_run",
        memory=memory,
    )
    better = next(item for item in adjusted if item.name == "Compliance Copilot")
    worse = next(item for item in adjusted if item.name == "Creator Bot")
    assert better.score > worse.score
    assert worse.signals["historical_failure_overlap"] >= better.signals["historical_failure_overlap"]


def test_historical_learning_preserves_exploration_signal(tmp_path):
    settings = _prepare_settings(tmp_path)
    settings.learning_exploration_rate = 0.25
    pipeline = VenturePipeline(settings)

    idea = Idea(
        name="Novel Workflow Miner",
        one_liner="Find new pain clusters",
        target_user="SMB teams",
        problem="Teams miss hidden bottlenecks",
        solution="Mine workflow telemetry",
        key_features=["novel", "workflow", "telemetry"],
    )
    score = IdeaScore(name="Novel Workflow Miner", score=68, rationale="base", risks=[], signals={})
    memory = pipeline._build_historical_learning_memory("workflow miner", run_id="r1")
    adjusted = pipeline._apply_historical_learning_to_scores(
        scores=[score],
        ideas=[idea],
        topic="workflow miner",
        run_id="r1",
        memory=memory,
    )
    assert "historical_exploration_rate" in adjusted[0].signals
    assert adjusted[0].signals["historical_exploration_rate"] == 0.25
