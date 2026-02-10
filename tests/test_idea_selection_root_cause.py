from pathlib import Path

from app.core.config import Settings
from app.core.models import SeedInputs
from app.core.pipeline import VenturePipeline


def test_select_idea_dicts_prefers_research_when_analysis_is_name_only(tmp_path: Path):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    pipeline = VenturePipeline(settings)

    analysis = {"ideas": [{"name": "Idea 1: Venture Ops Toolkit"}]}
    research = {
        "ideas": [
            {
                "name": "Idea 1: Venture Ops Toolkit",
                "one_liner": "Automate scoring and launch packs.",
                "target_user": "Small teams",
                "problem": "Idea prioritization is slow",
                "solution": "Collect signals and score ideas",
                "key_features": ["signals", "scoring", "launch pack"],
            }
        ]
    }

    selected = pipeline._select_idea_dicts(analysis, research)
    assert len(selected) == 1
    assert selected[0].get("problem") == "Idea prioritization is slow"

    ideas = pipeline._build_traceable_ideas(
        idea_dicts=selected,
        validated_pains=[
            {
                "id": "pain_1",
                "text": "Idea prioritization is slow",
                "actor": "Teams",
            }
        ],
        pages=[{"url": "https://example.com"}],
        seeds=SeedInputs(icp="Founders B2B SaaS pre-seed"),
    )
    assert len(ideas) == 1
