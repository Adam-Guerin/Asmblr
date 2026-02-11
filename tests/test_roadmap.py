from app.core.config import Settings
from app.core.models import IdeaScore
from app.core.pipeline import VenturePipeline


def _pipeline():
    return VenturePipeline(Settings())


def _sample_brand_payload():
    return {
        "project_name": "RoadmapX",
        "tagline": "Home for signal-led launches",
        "brand_direction": "precise, fast, and founder-friendly",
        "brand_keywords": ["signal", "roadmap", "launch"],
    }


def _sample_validated_pains():
    return [{"id": "pain_1", "text": "Manual decks waste time and context."}]


def _sample_opportunities():
    return [{"idea": {"name": "DeckPro"}, "score": {"score": 60}}]


def _sample_top_idea():
    return IdeaScore(
        name="RoadmapX",
        score=80,
        rationale="Maps signal-to-launch pipelines for solo founders.",
        risks=[],
        signals={},
    )


def test_generate_roadmap_default_phases():
    pipeline = _pipeline()
    roadmap = pipeline._generate_roadmap(
        "Launch orchestration tools",
        _sample_top_idea(),
        _sample_brand_payload(),
        _sample_validated_pains(),
        _sample_opportunities(),
        "Market blogs confirm demand for timely decks.",
    )

    assert roadmap["project_name"] == "RoadmapX"
    assert roadmap["topic"] == "Launch orchestration tools"
    assert len(roadmap["phases"]) >= 3
    assert any("Validation" in phase.get("name", "") for phase in roadmap["phases"])
    assert roadmap["key_metrics"]
    assert roadmap["assumptions"]


def test_format_roadmap_markdown_includes_sections():
    pipeline = _pipeline()
    roadmap = pipeline._generate_roadmap(
        "Launch orchestration tools",
        _sample_top_idea(),
        _sample_brand_payload(),
        _sample_validated_pains(),
        _sample_opportunities(),
        "Market blogs confirm demand for timely decks.",
    )
    markdown = pipeline._format_roadmap_markdown(roadmap)

    assert "# Roadmap" in markdown
    assert "## Key Metrics" in markdown
    assert "## Validation" in markdown or "Validation" in markdown
    assert "Assumptions" in markdown
