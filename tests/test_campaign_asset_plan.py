import json
from pathlib import Path

from app.core.config import Settings
from app.core.models import IdeaScore
from app.core.pipeline import VenturePipeline


def _mk_pipeline(tmp_path: Path) -> VenturePipeline:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    settings.campaign_auto_expand_assets = True
    settings.campaign_posts_target = 12
    settings.campaign_ads_target = 12
    settings.campaign_outreach_target = 4
    settings.campaign_videos_target = 2
    settings.campaign_target_assets = 30
    return VenturePipeline(settings)


def test_build_campaign_brief_uses_top_idea_details_from_opportunities(tmp_path: Path):
    pipeline = _mk_pipeline(tmp_path)
    run_id = pipeline.manager.create_run("campaign brief test")
    run_dir = Path(pipeline.manager.get_run(run_id)["output_dir"])
    pipeline.manager.write_artifact(
        run_id,
        "opportunities.json",
        json.dumps(
            {
                "items": [
                    {
                        "idea": {
                            "name": "Idea 1: Venture Ops Toolkit",
                            "one_liner": "Automate scoring and launch packs.",
                            "target_user": "Small teams",
                            "problem": "Idea prioritization is slow",
                            "solution": "Collect signals and score ideas",
                            "key_features": ["signals", "scoring", "launch pack"],
                        },
                        "score": {"name": "Idea 1: Venture Ops Toolkit", "score": 66},
                    }
                ]
            },
            indent=2,
        ),
    )
    brief = pipeline._build_campaign_brief(
        run_id,
        {"project_name": "Venture Ops Toolkit", "brand_keywords": ["pragmatic", "lean"]},
        IdeaScore(name="Idea 1: Venture Ops Toolkit", score=66, rationale="rationale", risks=[]),
    )
    assert brief["problem"] == "Idea prioritization is slow"
    assert brief["solution"] == "Collect signals and score ideas"
    assert brief["key_features"] == ["signals", "scoring", "launch pack"]


def test_campaign_expansion_hits_asset_targets(tmp_path: Path):
    pipeline = _mk_pipeline(tmp_path)
    brief = {
        "project_name": "Venture Ops Toolkit",
        "idea_name": "Idea 1: Venture Ops Toolkit",
        "target_user": "Small teams",
        "problem": "Idea prioritization is slow",
        "solution": "Collect signals and score ideas",
        "key_features": ["signals", "scoring", "launch pack"],
        "brand_keywords": ["pragmatic", "lean"],
    }

    posts = pipeline._expand_posts_for_campaign({}, brief)
    outreach = pipeline._expand_outreach_for_campaign({}, brief)
    videos = pipeline._expand_videos_for_campaign({}, brief)
    ads = pipeline._expand_ads_for_campaign({}, brief)

    posts_count = len(posts["x"]) + len(posts["linkedin"])
    outreach_count = len(outreach["email_sequence"]) + len(outreach["dm_sequence"])
    videos_count = len(videos["videos"])
    ads_count = len(ads["google_ads"]) + len(ads["meta_ads"]) + len(ads["tiktok_ads"])

    assert posts_count == 12
    assert outreach_count == 4
    assert videos_count == 2
    assert ads_count == 12
    assert posts_count + outreach_count + videos_count + ads_count == 30


def test_organic_winners_are_boosted_into_ads(tmp_path: Path):
    pipeline = _mk_pipeline(tmp_path)
    run_id = pipeline.manager.create_run("organic winner boost")
    posts_payload = {
        "x": [
            {"asset_id": "x_1", "text": "Validate your MVP faster", "cta": "Join early access", "hashtags": ["#mvp"]},
            {"asset_id": "x_2", "text": "Turn pains into launch assets", "cta": "Get launch pack", "hashtags": ["#startup"]},
        ],
        "linkedin": [
            {"asset_id": "linkedin_1", "text": "Founder workflow for pragmatic validation", "cta": "See plan", "hashtags": ["#founders"]},
        ],
    }
    publishing_payload = {
        "x": [{"likes": 1, "clicks": 2}, {"likes": 10, "clicks": 12}],
        "linkedin": [{"likes": 2, "clicks": 1}],
    }
    leaderboard = pipeline._build_organic_leaderboard(run_id, posts_payload, publishing_payload)
    assert leaderboard["winners"][0]["asset_id"] == "x_2"

    ads_payload = {
        "google_ads": [{"headline": "Base", "description": "Base", "final_url": ""}],
        "meta_ads": [{"primary_text": "Base", "headline": "Base", "description": "Base", "call_to_action": "LEARN_MORE", "landing_url": ""}],
        "tiktok_ads": [{"caption": "Base", "call_to_action": "Learn More", "landing_url": ""}],
    }
    boosted = pipeline._apply_organic_winners_to_ads(run_id, ads_payload)
    assert boosted.get("boosted_from_organic") is True
    assert "x_2" in boosted.get("organic_winner_ids", [])
    assert any(item.get("source_asset_id") == "x_2" for item in boosted.get("google_ads", []))
