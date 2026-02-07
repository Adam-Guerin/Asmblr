from typing import Any
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse


UNKNOWN_TOKENS = {"", "unknown", "n/a", "none", "null", "tbd", "todo"}


def _is_unknown_like(value: str | None) -> bool:
    return (value or "").strip().lower() in UNKNOWN_TOKENS


def _first_meaningful(*values: str, default: str) -> str:
    for value in values:
        text = (value or "").strip()
        if not _is_unknown_like(text):
            return text
    return default


def _domain_label(url: str | None, fallback: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return fallback
    parsed = urlparse(raw)
    return (parsed.netloc or raw).strip() or fallback


def extract_competitors(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    competitors = []
    for idx, page in enumerate(pages, start=1):
        html = page.get("text", "")
        soup = BeautifulSoup(html, "html.parser")
        url = page.get("url")
        source_label = _domain_label(url, fallback=f"source_{idx}")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""
        product_name = _first_meaningful(
            title,
            h1_text,
            source_label,
            default=f"competitor_{idx}",
        )[:80]

        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"].strip()

        raw_text = " ".join(soup.stripped_strings)
        lowered = raw_text.lower()

        positioning = meta_desc or ""
        if not positioning:
            for line in raw_text.split("\n"):
                line = line.strip()
                if len(line) >= 40:
                    positioning = line[:200]
                    break
        positioning = _first_meaningful(
            positioning,
            default="insufficient_evidence: positioning not explicit on the captured page",
        )

        # Pricing heuristics
        pricing = "insufficient_evidence: pricing not publicly listed"
        price_match = re.search(r"\\$\\s?\\d+(?:\\.\\d{2})?", raw_text)
        if price_match:
            pricing = f"mentions {price_match.group(0)}"
        elif "free trial" in lowered:
            pricing = "mentions free trial"
        elif "freemium" in lowered:
            pricing = "mentions freemium"
        elif "pricing" in lowered or "plans" in lowered or "billing" in lowered:
            pricing = "pricing page referenced"

        # Target users heuristics
        target_users = "segment_to_be_validated"
        for token in ["teams", "founders", "developers", "marketers", "designers", "operators", "sales", "support"]:
            if token in lowered:
                target_users = token
                break

        # Feature extraction: take up to 5 list items or headings
        key_features = []
        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            if 15 <= len(text) <= 120:
                key_features.append(text)
            if len(key_features) >= 5:
                break
        if not key_features:
            for tag in soup.find_all(["h2", "h3"]):
                text = tag.get_text(" ", strip=True)
                if 10 <= len(text) <= 80:
                    key_features.append(text)
                if len(key_features) >= 5:
                    break

        competitor = {
            "product_name": product_name,
            "positioning": positioning,
            "pricing": pricing,
            "features": key_features,
            "target": target_users,
            "evidence_urls": [url] if url else [],
            "evidence_quality": "high" if url and raw_text else "medium" if raw_text else "low",
            "next_step": "open official pricing page or product docs to confirm packaging and target segment",
        }
        competitors.append(competitor)
    return competitors
