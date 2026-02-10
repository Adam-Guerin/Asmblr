from pathlib import Path

from app.core.config import Settings
from app.core.models import Idea, IdeaScore, SeedInputs
from app.core.pipeline import VenturePipeline


def _make_pipeline(tmp_path: Path) -> VenturePipeline:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    settings.primary_icp = "Founders B2B SaaS pre-seed"
    return VenturePipeline(settings)


def test_derive_ideas_from_structured_opportunities(tmp_path: Path):
    pipeline = _make_pipeline(tmp_path)
    opportunities = [
        {
            "name": "Founders onboarding opportunity",
            "target_actor": "Founders",
            "linked_pains": ["pain_1"],
            "source_urls": ["https://example.com/thread"],
            "assumptions": ["Assumes pain_1 is frequent."],
        }
    ]
    validated_pains = [
        {
            "id": "pain_1",
            "text": "Founders struggle to prioritize experiments each week.",
            "intensity_signal": 60,
            "frequency_signal": 40,
        }
    ]
    ideas = pipeline._derive_ideas_from_structured_opportunities(
        opportunities,
        validated_pains,
        SeedInputs(icp="Founders B2B SaaS pre-seed"),
        limit=2,
    )
    assert len(ideas) == 1
    assert ideas[0]["pain_ids"] == ["pain_1"]
    assert ideas[0]["problem"] == "Founders struggle to prioritize experiments each week."


def test_apply_pragmatic_potential_to_scores_enriches_signals(tmp_path: Path):
    pipeline = _make_pipeline(tmp_path)
    idea = Idea(
        name="Idea 1",
        one_liner="Validate demand with a landing and interviews",
        target_user="Founders B2B SaaS pre-seed",
        problem="Founders struggle to prioritize experiments each week.",
        solution="Ship a test workflow with metrics",
        key_features=["landing page", "interview loop", "weekly scoring"],
        pain_ids=["pain_1", "pain_2"],
        sources=["https://a.com/post", "https://b.com/post"],
        hypotheses=["Assumes repeated demand signal."],
    )
    scores = [IdeaScore(name="Idea 1", score=60, rationale="Baseline", risks=[], signals={})]
    validated_pains = [
        {"id": "pain_1", "intensity_signal": 70, "frequency_signal": 50},
        {"id": "pain_2", "intensity_signal": 65, "frequency_signal": 45},
    ]
    updated = pipeline._apply_pragmatic_potential_to_scores(scores, [idea], validated_pains)
    assert len(updated) == 1
    assert "pragmatic_potential" in updated[0].signals
    assert 0 <= updated[0].score <= 100
