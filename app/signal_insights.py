from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Tuple

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

ACTOR_PATTERN = re.compile(
    r"\b(?P<actor>(?:teams?|operators?|founders?|managers?|developers?|customers?|users?|businesses?|companies?|builders?))\b",
    re.IGNORECASE,
)
CONTEXT_PATTERN = re.compile(
    r"\b(?P<context>during|while|when|after|before|in|at|within|throughout)\b", re.IGNORECASE
)
WORKAROUND_PATTERN = re.compile(
    r"\b(currently|right now|today|using|via|manually|with spreadsheets|for now)\b", re.IGNORECASE
)


def _split_sentences(text: str) -> List[str]:
    candidate = re.split(r"[.!?\n]+", text or "")
    return [sentence.strip() for sentence in candidate if len(sentence.strip()) > 30]


def _find_actor(sentence: str) -> str:
    match = ACTOR_PATTERN.search(sentence)
    if not match:
        return ""
    return match.group("actor").capitalize()


def _find_context(sentence: str) -> str:
    match = CONTEXT_PATTERN.search(sentence)
    if not match:
        return ""
    return match.group("context")


def _find_workaround(sentence: str) -> str:
    match = WORKAROUND_PATTERN.search(sentence)
    if not match:
        return "Manual workarounds (spreadsheets, meetings)"
    return match.group(0)


def _score_intensity(sentence: str) -> int:
    words = len(sentence.split())
    return min(100, max(10, words * 2))


def _score_frequency(text: str, counts: Counter) -> int:
    frequency = counts.get(text.lower(), 1)
    return min(100, frequency * 10)


def extract_structured_pains(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    sentences: List[Tuple[str, Dict[str, Any]]] = []
    for page in pages:
        text = page.get("text", "")
        for sentence in _split_sentences(text):
            sentences.append((sentence, page))

    counts = Counter(sentence.lower() for sentence, _ in sentences)

    pains: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    seen: set[str] = set()
    counter = 0
    for sentence, page in sentences:
        normalized = sentence.strip()
        if normalized.lower() in seen:
            continue
        seen.add(normalized.lower())

        actor = _find_actor(normalized)
        if not actor:
            rejected.append({"text": normalized, "reason": "missing actor"})
            continue

        problem = normalized
        if not problem:
            rejected.append({"text": normalized, "reason": "missing problem"})
            continue

        context = _find_context(normalized)
        workaround = _find_workaround(normalized)
        frequency = _score_frequency(normalized, counts)
        intensity = _score_intensity(normalized)

        counter += 1
        snippet = normalized if len(normalized) <= 200 else normalized[:200] + "…"
        pain = {
            "id": f"pain_{counter}",
            "actor": actor,
            "context": context,
            "problem": problem,
            "text": problem,
            "current_workaround": workaround,
            "frequency_signal": frequency,
            "intensity_signal": intensity,
            "source_urls": [page.get("url")],
            "quote_snippets": [snippet],
            "difficulty": "concrete",
        }
        pains.append(pain)

    return {"pains": pains, "rejected": rejected}


def cluster_pains(pains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    problems = [pain["problem"] for pain in pains if pain.get("problem")]
    if not problems:
        return []

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(problems)
    n_clusters = min(max(1, len(problems) // 2), len(problems))
    if n_clusters == 0:
        n_clusters = 1

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)
    feature_names = vectorizer.get_feature_names_out()

    clusters: List[Dict[str, Any]] = []
    for cluster_id in sorted(set(labels)):
        cluster_pains = [
            pains[idx] for idx, label in enumerate(labels) if label == cluster_id
        ]
        if not cluster_pains:
            continue

        centroid = model.cluster_centers_[cluster_id]
        sorted_terms = sorted(zip(centroid, feature_names), reverse=True)[:4]
        keywords = [term for _, term in sorted_terms if term]
        job_label = f"Job {cluster_id + 1}: {' / '.join(keywords[:2]) or 'signals'}"
        clusters.append(
            {
                "cluster_id": int(cluster_id),
                "cluster_label": job_label,
                "pain_ids": [pain["id"] for pain in cluster_pains],
                "keywords": keywords,
                "density": int(len(cluster_pains)),
            }
        )

    return clusters


def generate_opportunities(
    clusters: List[Dict[str, Any]], pains: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    pain_map = {pain["id"]: pain for pain in pains}
    opportunities: List[Dict[str, Any]] = []

    for cluster in clusters:
        linked = cluster.get("pain_ids", [])
        if not linked:
            continue
        actors = [pain_map[pid]["actor"] for pid in linked if pain_map.get(pid)]
        target_actor = actors[0] if actors else "Operators"
        source_urls = sorted(
            {
                url
                for pid in linked
                for url in (pain_map.get(pid, {}).get("source_urls") or [])
                if url
            }
        )
        keywords = cluster.get("keywords", [])[:3]
        why_now = (
            f"{cluster.get('density', len(linked))} signals from structured scraping show the urgency."
        )
        differentiation = (
            f"Blend {', '.join(keywords)} with unique data to stand out." if keywords else "Focus on triage."
        )
        assumptions = [
            f"Assumes pains {', '.join(linked[:3])} reflect {target_actor.lower()} priorities.",
            "Assumes source signals remain consistent over the next 30-60 days.",
        ]
        for idx in range(min(3, max(1, len(linked)))):
            opportunity = {
                "name": f"{target_actor} {cluster['cluster_label']} opportunity #{idx + 1}",
                "target_actor": target_actor,
                "jtbd": f"Help {target_actor.lower()} {cluster['cluster_label'].lower()} batteries of pain.",
                "linked_pains": linked,
                "source_urls": source_urls[:10],
                "assumptions": assumptions,
                "why_now": why_now,
                "differentiation_hint": differentiation,
                "risks": [
                    "Requires validation via interviews",
                    "Data signal exposure may fluctuate",
                ],
            }
            opportunities.append(opportunity)

    return opportunities
