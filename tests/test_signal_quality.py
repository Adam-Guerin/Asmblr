from app.core.config import Settings
from app.core.prerun_gate import PreRunGate
from app.signal_quality import compute_novelty_score, compute_signal_quality


def test_compute_signal_quality_components():
    settings = Settings()
    raw_pages = [
        {
            "url": "https://news.example/recent",
            "text": "Operators struggle to keep compliance data synced across dashboards.",
            "source_name": "News",
            "pass_type": "recent",
        },
        {
            "url": "https://news.example/top",
            "text": "Operations teams need faster approvals now.",
            "source_name": "News",
            "pass_type": "top",
        },
        {
            "url": "https://forum.example/thread",
            "text": "Managers juggle spreadsheets to track supplier risk.",
            "source_name": "Forum",
            "pass_type": "search",
        },
    ]
    structured_pains = [
        {
            "id": "pain_1",
            "problem": "Operators struggle to keep compliance data synced across dashboards.",
            "source_urls": ["https://news.example/recent"],
        },
        {
            "id": "pain_2",
            "problem": "Managers juggle spreadsheets to track supplier risk.",
            "source_urls": ["https://forum.example/thread"],
        },
    ]
    clusters = [
        {"cluster_id": 0, "pain_ids": ["pain_1"], "keywords": ["compliance"], "density": 1},
        {"cluster_id": 1, "pain_ids": ["pain_2"], "keywords": ["risk"], "density": 1},
    ]

    novelty = compute_novelty_score(raw_pages, structured_pains, settings)
    quality = compute_signal_quality(raw_pages, structured_pains, clusters, novelty["novelty_score"], settings)
    assert 0 <= quality["score"] <= 100
    assert quality["breakdown"]["novelty"]["value"] == novelty["novelty_score"]
    assert novelty["breakdown"]["multi_platform_ratio"] >= 0


def test_gate_blocks_low_signal_quality():
    gate = PreRunGate(min_pages=0, min_pains=0, min_competitors=0, min_signal_quality=50)
    result = gate.evaluate([], [], [], "", {}, signal_quality={"score": 30})
    assert not result.ok
    assert any("signal quality" in reason for reason in result.reasons)
