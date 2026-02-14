import json
from unittest.mock import MagicMock

from app.core.config import Settings
from app.core.pipeline import VenturePipeline


def _sample_posts():
    return {
        "x": [
            {
                "asset_id": "x_1",
                "text": "Manual decks slow every launch. This automates the build.",
            }
        ],
        "linkedin": [
            {
                "asset_id": "linkedin_1",
                "text": "We ship pitch decks and landing pages in one sprint.",
            }
        ],
    }


def _pipeline():
    return VenturePipeline(Settings())


def test_social_metrics_simulates_posts_when_api_missing():
    pipeline = _pipeline()
    performance = pipeline._fetch_social_post_performance("run_social", _sample_posts())
    assert "x" in performance
    assert "linkedin" in performance
    assert isinstance(performance["x"][0].get("ctr"), float)
    assert performance["x"][0]["ctr"] >= 0.0
    assert performance["linkedin"][0]["impressions"] > 0


def test_social_apply_marks_best_variant_for_ads():
    pipeline = _pipeline()
    posts = _sample_posts()
    performance = pipeline._fetch_social_post_performance("run_social", posts)
    best = pipeline._apply_social_performance(posts, performance)

    assert posts["x"][0]["performance"]["asset_id"] == "x_1"
    assert "ads_priority" in posts["x"][0]
    assert best["x"]["asset_id"] == posts["x"][0]["asset_id"]
    assert best["linkedin"]["asset_id"] == posts["linkedin"][0]["asset_id"]


def test_social_performance_markdown_includes_summary():
    pipeline = _pipeline()
    performance = pipeline._fetch_social_post_performance("run_social", _sample_posts())
    markdown = pipeline._format_social_performance_markdown(performance)
    assert "# Social Performance" in markdown
    assert "CTR" in markdown.upper() or "ctr" in markdown
    assert "engagement" in markdown.lower()


def test_social_followup_records_best_assets(tmp_path):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = tmp_path / "configs"
    pipeline = VenturePipeline(settings)
    run_id = pipeline.manager.create_run("followup")
    posts = {
        "x": [
            {
                "asset_id": "x_test",
                "platform": "x",
                "text": "Post 1",
                "ads_recommendation": True,
                "performance": {"score": 0.5},
                "ads_priority": "high",
                "created_at": "2026-02-11T00:00:00Z",
            }
        ]
    }
    best_entries = {"x": {"asset_id": "x_test", "score": 0.5, "ctr": 0.03}}

    pipeline._persist_social_followup(run_id, posts, best_entries)

    followup_path = settings.runs_dir / run_id / "distribution" / "social_followup.json"
    assert followup_path.exists()
    data = json.loads(followup_path.read_text())
    assert data["best_social_assets"]["x"]["asset_id"] == "x_test"
    record = data["records"][0]
    assert record["ads_recommendation"]
    assert float(record["performance"]["score"]) == 0.5


def test_ads_booster_history_records_best_assets(tmp_path):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = tmp_path / "configs"
    pipeline = VenturePipeline(settings)
    run_id = pipeline.manager.create_run("ads_history")
    posts = {
        "x": [
            {
                "asset_id": "x_best",
                "platform": "x",
                "text": "Best post",
                "ads_recommendation": True,
                "created_at": "2026-02-11T00:00:00Z",
                "hashtags": ["#test"],
                "final_url": "https://example.com",
                "cta": "Learn more",
            }
        ]
    }
    best_entries = {"x": {"asset_id": "x_best", "score": 0.2, "ctr": 0.05, "source": "simulated"}}

    pipeline._record_ads_booster_history(run_id, posts, best_entries)

    history_path = settings.runs_dir / run_id / "distribution" / "ads_booster_history.json"
    assert history_path.exists()
    data = json.loads(history_path.read_text())
    assert data["records"][0]["status"] == "queued"
    assert data["records"][0]["platform"] == "x"
    assert data["records"][0]["asset_id"] == "x_best"
    assert data["records"][0]["hashtags"] == ["#test"]


def test_social_performance_adapter_used(monkeypatch):
    adapter = MagicMock()
    adapter.fetch.return_value = {
        "x": [{"asset_id": "x_1", "ctr": 0.08, "score": 0.12}]
    }
    monkeypatch.setattr("app.core.pipeline.build_social_metrics_adapter", lambda settings: adapter)

    pipeline = _pipeline()
    posts = _sample_posts()
    performance = pipeline._fetch_social_post_performance("run_social", posts)

    adapter.fetch.assert_called_once_with("run_social", posts)
    assert performance["x"][0]["asset_id"] == "x_1"
    assert performance["x"][0]["source"] == "api"
    assert performance["x"][0]["platform"] == "x"


def test_social_performance_adapter_failure_falls_back(monkeypatch):
    adapter = MagicMock()
    adapter.fetch.side_effect = RuntimeError("adapter fail")
    monkeypatch.setattr("app.core.pipeline.build_social_metrics_adapter", lambda settings: adapter)

    pipeline = _pipeline()
    posts = _sample_posts()
    performance = pipeline._fetch_social_post_performance("run_social", posts)

    adapter.fetch.assert_called_once()
    assert performance["x"][0]["source"] == "simulated"
    assert isinstance(performance["x"][0]["ctr"], float)
