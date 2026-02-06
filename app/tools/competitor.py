from typing import List, Dict, Any
from bs4 import BeautifulSoup
import re


def extract_competitors(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    competitors = []
    for page in pages:
        html = page.get("text", "")
        soup = BeautifulSoup(html, "html.parser")
        url = page.get("url", "unknown")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""
        product_name = (title or h1_text or url).strip()[:80] or "unknown"

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
        positioning = positioning or "unknown"

        # Pricing heuristics
        pricing = "unknown"
        price_match = re.search(r"\\$\\s?\\d+(?:\\.\\d{2})?", raw_text)
        if price_match:
            pricing = f"mentions {price_match.group(0)}"
        elif "pricing" in lowered or "plans" in lowered or "billing" in lowered:
            pricing = "pricing page referenced"

        # Target users heuristics
        target_users = "unknown"
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
            "evidence_urls": [url],
        }
        competitors.append(competitor)
    return competitors
