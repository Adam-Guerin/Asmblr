from app.core.config import Settings
from app.core.models import IdeaScore
from app.core.pipeline import VenturePipeline


def _sample_pipeline():
    settings = Settings()
    pipeline = VenturePipeline(settings)
    return pipeline


def _sample_brand_payload():
    return {
        "project_name": "PitchFlow",
        "tagline": "Decks in minutes",
        "brand_direction": "fast clarity",
        "brand_keywords": ["clear", "fast", "founder-first"],
    }


def _sample_validated_pains():
    return [{"id": "pain_1", "text": "Manual decks waste time and context."}]


def _sample_competitors():
    return [{"product_name": "DeckPro", "pricing": "$29/mo"}]


def _sample_top_idea():
    return IdeaScore(
        name="PitchFlow",
        score=82,
        rationale="Automates investor communications for solopreneurs.",
        risks=[],
        signals={},
    )


def test_generate_pitch_deck_fallback_structure():
    pipeline = _sample_pipeline()
    topic = "Pitch automation tools"
    deck = pipeline._generate_pitch_deck(
        topic,
        _sample_top_idea(),
        _sample_brand_payload(),
        "Conversations with founders highlight opportunity for structured decks.",
        _sample_validated_pains(),
        _sample_competitors(),
    )

    assert deck["project_name"] == "PitchFlow"
    assert deck["topic"] == topic
    assert len(deck["slides"]) == 7
    assert deck["slides"][1]["title"] == "Problem"
    assert "Manual decks" in deck["slides"][1]["summary"] or any(
        "Manual decks" in bullet for bullet in deck["slides"][1]["bullets"]
    )
    assert deck["ask"]["amount"] == "TBD"


def test_format_pitch_deck_markdown_includes_sections():
    pipeline = _sample_pipeline()
    deck = pipeline._generate_pitch_deck(
        "Pitch automation tools",
        _sample_top_idea(),
        _sample_brand_payload(),
        "Market scan shows 3 adjacent manual workflows.",
        _sample_validated_pains(),
        _sample_competitors(),
    )
    markdown = pipeline._format_pitch_deck_markdown(deck)

    assert "# Pitch Deck" in markdown
    assert "## Key Metrics" in markdown
    assert "## Ask" in markdown
    assert "- Amount: TBD" in markdown
