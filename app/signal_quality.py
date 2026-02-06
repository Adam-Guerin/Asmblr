from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Set

from app.core.config import Settings


def _tokenize(text: str) -> List[str]:
    text = text.lower() or ""
    tokens = re.findall(r"\b[a-z]{5,}\b", text)
    return tokens


def compute_novelty_score(
    raw_pages: List[Dict[str, Any]],
    structured_pains: List[Dict[str, Any]],
    settings: Settings,
) -> Dict[str, Any]:
    token_counts: Counter[str] = Counter()
    for page in raw_pages:
        token_counts.update(_tokenize(page.get("text", "")))

    novel_keywords: List[str] = [
        token for token, count in token_counts.items() if count == 1
    ]
    novel_keywords = novel_keywords[: settings.signal_novel_keywords_target]
    novel_ratio = min(
        1.0,
        len(novel_keywords) / max(1, settings.signal_novel_keywords_target),
    )

    url_to_source = {}
    for page in raw_pages:
        if page.get("url") and page.get("source_name"):
            url_to_source[page["url"]] = page["source_name"]

    multi_platform = 0
    for pain in structured_pains:
        sources = {
            url_to_source.get(url)
            for url in pain.get("source_urls", [])
            if url_to_source.get(url)
        }
        sources.discard(None)
        if len(sources) >= 2:
            multi_platform += 1
    multi_platform_ratio = (
        multi_platform / max(1, len(structured_pains)) if structured_pains else 0.0
    )

    recent_pages = [
        page for page in raw_pages if page.get("pass_type") == "recent"
    ]
    recency_ratio = len(recent_pages) / max(1, len(raw_pages)) if raw_pages else 0.0

    novelty_value = min(
        1.0,
        0.5 * novel_ratio + 0.35 * multi_platform_ratio + 0.15 * recency_ratio,
    )
    score = int(round(novelty_value * 20))

    return {
        "novelty_score": score,
        "breakdown": {
            "novel_keywords": {"value": len(novel_keywords), "max": settings.signal_novel_keywords_target},
            "multi_platform_ratio": round(multi_platform_ratio, 2),
            "recency_ratio": round(recency_ratio, 2),
        },
        "keywords": novel_keywords,
    }


def compute_signal_quality(
    raw_pages: List[Dict[str, Any]],
    structured_pains: List[Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    novelty_score: int,
    settings: Settings,
) -> Dict[str, Any]:
    unique_sources = {page.get("source_name") for page in raw_pages if page.get("source_name")}
    volume = len(raw_pages)
    unique_pains = {
        pain["problem"].lower()
        for pain in structured_pains
        if pain.get("problem")
    }

    volume_score = min(20, int(round(min(1.0, volume / max(1, settings.signal_pages_target)) * 20)))
    diversity_score = min(20, int(round(min(1.0, len(unique_sources) / max(1, settings.signal_sources_target)) * 20)))
    repeat_ratio = 0.0
    if structured_pains:
        repeat_ratio = min(
            1.0,
            (len(structured_pains) / max(1, len(unique_pains))) / max(1, settings.signal_repeat_target),
        )
    repeat_score = min(20, int(round(repeat_ratio * 20)))

    cluster_density = 0.0
    if clusters:
        total_pains = sum(len(cluster.get("pain_ids", [])) for cluster in clusters)
        cluster_density = total_pains / len(clusters) if clusters else 0.0
    density_score = min(
        20,
        int(round(min(1.0, cluster_density / max(1, settings.signal_cluster_density_target)) * 20)),
    )

    novelty_component = min(20, int(round(min(1.0, novelty_score / 20) * 20)))

    total_score = volume_score + diversity_score + repeat_score + density_score + novelty_component
    return {
        "score": total_score,
        "breakdown": {
            "volume": {"score": volume_score, "max": 20, "value": volume},
            "diversity": {"score": diversity_score, "max": 20, "value": len(unique_sources)},
            "repetition": {"score": repeat_score, "max": 20, "value": len(structured_pains)},
            "cluster_density": {"score": density_score, "max": 20, "value": round(cluster_density, 2)},
            "novelty": {"score": novelty_component, "max": 20, "value": novelty_score},
        },
    }
