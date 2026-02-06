import json
from pathlib import Path
from datetime import datetime, timezone

from app.core.config import Settings
from app.signal_engine import SignalEngine


def _build_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.max_sources = 4
    settings.request_timeout = 1
    settings.rate_limit_per_domain = 10
    settings.retry_max_attempts = 1
    settings.retry_min_wait = 1
    settings.retry_max_wait = 2
    return settings


def test_signal_engine_writes_raw_pages(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)
    run_dir = settings.runs_dir / "run-signal"
    sources = [{"name": "News", "url": "https://example.com"}]

    def fetcher(pass_type, sources_list, limit, topic):
        src = sources_list[0]
        return [
            {
                "url": f"{src['url']}/{pass_type}",
                "text": f"signal {pass_type}",
                "name": f"{pass_type} page",
                "fingerprint": 999,
            }
        ]

    engine = SignalEngine(settings, run_dir, topic="automation", fast_mode=True, fetcher=fetcher)
    result = engine.run(sources)
    assert len(result.raw_pages) == 3
    raw_path = run_dir / "raw_pages.json"
    assert raw_path.exists()
    payload = json.loads(raw_path.read_text())
    assert all(entry["pass_type"] in ("recent", "top", "search") for entry in payload["pages"])
    assert payload["pages"][0]["source_name"] == "News"


def test_signal_engine_deduplication(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)
    run_dir = settings.runs_dir / "run-dup"
    sources = [{"name": "Forum", "url": "https://forum.example"}]

    def fetcher(pass_type, sources_list, limit, topic):
        text = "Teams need faster ops" if pass_type != "top" else "Teams need faster ops with automation detail"
        return [
            {
                "url": f"{sources_list[0]['url']}/{pass_type}",
                "text": text,
                "name": f"{pass_type}",
                "fingerprint": 42,
            }
        ]

    engine = SignalEngine(settings, run_dir, topic="ops", fetcher=fetcher)
    result = engine.run(sources)
    dedup_path = run_dir / "pages_deduped.json"
    assert dedup_path.exists()
    payload = json.loads(dedup_path.read_text())
    assert len(payload["groups"]) == 1
    assert payload["groups"][0]["canonical"]["pass_type"] == "top"
    assert result.deduped_pages[0]["pass_type"] == "top"
    duplicates = payload["groups"][0]["duplicates"]
    assert any(dup["pass_type"] != "top" for dup in duplicates)


def test_signal_engine_strict_recency_blocks_missing_dates(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)
    run_dir = settings.runs_dir / "run-strict-recency"
    source = {
        "name": "Strict Source",
        "url": "https://example.com",
        "strict_recency": True,
        "recency_days": 30,
    }

    def fetcher(pass_type, sources_list, limit, topic):
        return [{"url": "https://example.com/x", "text": "fresh pain signals", "name": "x"}]

    engine = SignalEngine(settings, run_dir, topic="ops", fetcher=fetcher)
    result = engine.run([source])
    assert result.raw_pages == []


def test_signal_engine_recency_weight_affects_score(tmp_path: Path) -> None:
    settings = _build_settings(tmp_path)
    run_dir = settings.runs_dir / "run-weight"
    engine = SignalEngine(settings, run_dir, topic="ops")
    now = datetime.now(timezone.utc).isoformat()
    text = "Teams struggle with manual onboarding and repetitive support escalations."

    low = engine._compute_signal_score(
        text=text,
        pass_type="recent",
        published_at=now,
        upvotes=0,
        comments_count=0,
        source={"recency_weight": 0.5},
    )
    high = engine._compute_signal_score(
        text=text,
        pass_type="recent",
        published_at=now,
        upvotes=0,
        comments_count=0,
        source={"recency_weight": 2.5},
    )
    assert high > low


def test_signal_engine_reddit_api_parsing(tmp_path: Path, monkeypatch) -> None:
    settings = _build_settings(tmp_path)
    run_dir = settings.runs_dir / "run-reddit"
    engine = SignalEngine(settings, run_dir, topic="onboarding")
    sample_payload = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Founders struggle with activation",
                        "selftext": "Activation drops after signup.",
                        "permalink": "/r/SaaS/comments/abc123/test/",
                        "created_utc": datetime.now(timezone.utc).timestamp(),
                        "ups": 42,
                        "num_comments": 11,
                    }
                }
            ]
        }
    }

    monkeypatch.setattr(
        "app.tools.web.WebSearchAndSummarize.fetch_url",
        lambda self, url, headers=None: json.dumps(sample_payload),
    )
    source = {
        "name": "Reddit API r/SaaS",
        "api": "reddit",
        "url": "https://www.reddit.com/r/SaaS/",
        "templates": {"recent": "https://www.reddit.com/r/SaaS/new.json?limit={limit}"},
        "strict_recency": True,
        "recency_days": 30,
        "limit": 10,
    }
    result = engine.run([source])
    assert result.raw_pages
    first = result.raw_pages[0]
    assert first["url"].startswith("https://www.reddit.com/r/SaaS/comments/")
    assert "activation" in first["text"].lower()
