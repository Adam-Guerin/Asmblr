from __future__ import annotations

import hashlib
import json
import re
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Callable
from urllib.parse import quote_plus
from datetime import datetime, timezone, timedelta

from app.core.config import Settings
from app.tools.web import WebSearchAndSummarize, WebSource
from loguru import logger

Fetcher = Callable[[str, list[dict[str, str]], int, str], list[dict[str, Any]]]


def _simhash(text: str, bits: int = 64) -> int:
    tokens = re.findall(r"\w+", text.lower()) if text else []
    if not tokens:
        return 0
    vector = [0] * bits
    for token in tokens:
        token_hash = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
        for i in range(bits):
            bit = (token_hash >> i) & 1
            vector[i] += 1 if bit else -1
    fingerprint = 0
    for i, value in enumerate(vector):
        if value >= 0:
            fingerprint |= 1 << i
    return fingerprint


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _score_text(text: str, pass_type: str, weight_map: dict[str, float] | None = None) -> int:
    weight_map = weight_map or {"recent": 1.0, "top": 1.2, "search": 1.1}
    weight = weight_map.get(pass_type, 1.0)
    words = re.findall(r"\w+", text) if text else []
    return int(len(words) * weight)


@dataclass
class SignalEngineResult:
    raw_pages: list[dict[str, Any]]
    deduped_pages: list[dict[str, Any]]
    groups: list[dict[str, Any]]


class SignalEngine:
    PASSES = ["recent", "top", "search"]

    def __init__(
        self,
        settings: Settings,
        output_dir: Path,
        topic: str,
        fast_mode: bool = False,
        fetcher: Fetcher | None = None,
    ) -> None:
        self.settings = settings
        self.output_dir = Path(output_dir)
        self.topic = topic
        self.fast_mode = fast_mode
        self.fetcher = fetcher or self._default_fetcher
        self._hamming_threshold = 10

    def run(self, sources: list[dict[str, str]]) -> SignalEngineResult:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        raw_pages: list[dict[str, Any]] = []
        if not self.topic or not isinstance(self.topic, str):
            logger.warning("Signal engine topic is empty or invalid.")
        max_sources = max(1, self.settings.max_sources)
        limit = min(3, max_sources) if self.fast_mode else max_sources
        for pass_type in self.PASSES:
            pass_pages = self._run_pass(pass_type, sources, limit)
            raw_pages.extend(pass_pages)

        self._write_json({"pages": raw_pages}, "raw_pages.json")
        groups = self._dedupe(raw_pages)
        self._write_json({"groups": groups, "summary": {"total_pages": len(raw_pages), "unique": len(groups)}}, "pages_deduped.json")
        deduped_pages = [group["canonical"] for group in groups]
        return SignalEngineResult(raw_pages=raw_pages, deduped_pages=deduped_pages, groups=groups)

    def _run_pass(self, pass_type: str, sources: list[dict[str, str]], limit: int) -> list[dict[str, Any]]:
        if not sources:
            return []
        per_source_limit = max(1, limit // len(sources))
        normalized = []
        for source in sources:
            if not source.get("name") or not source.get("url"):
                logger.warning("Skipping invalid source entry: {source}", source=source)
                continue
            entries = self.fetcher(pass_type, [source], per_source_limit, self.topic)
            for entry in entries:
                page = self._normalize_entry(entry, source, pass_type)
                if self._is_recent_enough(page, source):
                    normalized.append(page)
        return normalized

    def _normalize_entry(self, entry: dict[str, Any], source: dict[str, str], pass_type: str) -> dict[str, Any]:
        text = str(entry.get("text") or entry.get("summary") or "")
        fingerprint = entry.get("fingerprint")
        if fingerprint is None:
            fingerprint = _simhash(text)
        published_at = entry.get("published_at")
        if published_at:
            try:
                published_at = self._normalize_datetime(str(published_at))
            except Exception:
                published_at = entry.get("published_at")
        upvotes = entry.get("upvotes")
        comments_count = entry.get("comments_count")
        signal_score = self._compute_signal_score(
            text=text,
            pass_type=pass_type,
            published_at=published_at,
            upvotes=upvotes,
            comments_count=comments_count,
            source=source,
        )
        page = {
            "url": entry.get("url") or source["url"],
            "title": entry.get("title") or entry.get("name") or source["name"],
            "source_name": source["name"],
            "text": text,
            "pass_type": pass_type,
            "published_at": published_at,
            "upvotes": upvotes,
            "comments_count": comments_count,
            "signal_score": signal_score,
            "fingerprint": fingerprint,
        }
        return page

    def _dedupe(self, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = []
        for page in pages:
            fingerprint = page.get("fingerprint", 0)
            group = next(
                (g for g in groups if _hamming(g["fingerprint"], fingerprint) <= self._hamming_threshold),
                None,
            )
            if not group:
                group = {"group_id": len(groups) + 1, "fingerprint": fingerprint, "pages": []}
                groups.append(group)
            group["pages"].append(page)

        result = []
        for group in groups:
            canonical = max(group["pages"], key=lambda p: (p.get("signal_score", 0), len(p.get("text", ""))))
            duplicates = [
                {"url": p["url"], "signal_score": p.get("signal_score", 0), "pass_type": p.get("pass_type")}
                for p in group["pages"]
                if p["url"] != canonical["url"]
            ]
            result.append({"group_id": group["group_id"], "fingerprint": group["fingerprint"], "canonical": canonical, "duplicates": duplicates})
        return result

    def _normalize_datetime(self, value: str) -> str | None:
        if not value:
            return None
        text = value.strip()
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            dt = datetime.fromisoformat(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            return None

    def _compute_signal_score(
        self,
        text: str,
        pass_type: str,
        published_at: str | None,
        upvotes: Any,
        comments_count: Any,
        source: dict[str, Any] | None = None,
    ) -> int:
        source = source or {}
        words = re.findall(r"\w+", text) if text else []
        length_ratio = min(1.0, len(words) / 400.0)
        weight_map = {"recent": 1.0, "top": 1.2, "search": 1.1}
        length_score = 60.0 * length_ratio * weight_map.get(pass_type, 1.0)

        try:
            upvotes_val = int(upvotes) if upvotes is not None else 0
        except Exception:
            upvotes_val = 0
        try:
            comments_val = int(comments_count) if comments_count is not None else 0
        except Exception:
            comments_val = 0
        engagement_raw = upvotes_val + (comments_val * 2)
        engagement_ratio = min(1.0, engagement_raw / 50.0)
        engagement_score = 25.0 * engagement_ratio

        recency_score = 0.0
        recency_weight = float(source.get("recency_weight") or 1.0)
        recency_weight = max(0.5, min(3.0, recency_weight))
        if published_at:
            try:
                text_dt = published_at
                if isinstance(text_dt, str) and text_dt.endswith("Z"):
                    text_dt = text_dt[:-1] + "+00:00"
                dt = datetime.fromisoformat(str(text_dt))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                days = int(source.get("recency_days") or self.settings.signal_recency_days)
                if days > 0:
                    delta_days = (datetime.now(timezone.utc) - dt).days
                    half_life = max(1.0, days / 3.0)
                    recency_ratio = math.exp(-max(0.0, delta_days) / half_life)
                    if delta_days > (days * 3):
                        recency_ratio = 0.0
                    recency_score = 25.0 * recency_ratio * recency_weight
            except Exception:
                recency_score = 0.0

        total = length_score + engagement_score + recency_score
        return int(round(max(0.0, min(100.0, total))))

    def _default_fetcher(self, pass_type: str, sources: list[dict[str, str]], limit: int, topic: str) -> list[dict[str, Any]]:
        primary_source = sources[0] if sources else {}
        source_api = str(primary_source.get("api") or "").strip().lower()
        if source_api == "reddit":
            return self._fetch_reddit_api(primary_source, pass_type, limit, topic)
        if source_api == "github_issues":
            return self._fetch_github_issues_api(primary_source, limit, topic)

        cache_root = self.settings.data_dir / "cache" / "signal_engine" / pass_type
        tool = WebSearchAndSummarize(
            [],
            cache_dir=cache_root,
            timeout=self.settings.request_timeout,
            rate_limit_per_domain=self.settings.rate_limit_per_domain,
            retry_max_attempts=self.settings.retry_max_attempts,
            retry_min_wait=self.settings.retry_min_wait,
            retry_max_wait=self.settings.retry_max_wait,
        )
        if pass_type == "search":
            results: list[dict[str, Any]] = []
            per_source_limit = max(1, limit // max(1, len(sources)))
            for source in sources:
                if not source.get("url"):
                    continue
                query = f"site:{source['url']} {topic}".strip()
                results.extend(tool.search_bing(query, limit=per_source_limit))
            return results
        expanded_sources: list[WebSource] = []
        for source in sources:
            urls = self._expand_source_urls(tool, source, pass_type, topic, limit)
            for url in urls:
                expanded_sources.append(WebSource(name=f"{source['name']} ({pass_type})", url=url))
        tool.sources = expanded_sources
        return tool.run(max_sources=limit)

    def _expand_source_urls(
        self,
        tool: WebSearchAndSummarize,
        source: dict[str, Any],
        pass_type: str,
        topic: str,
        limit: int,
    ) -> list[str]:
        urls: list[str] = []
        base_url = source.get("url")
        if base_url:
            urls.append(self._build_pass_url(base_url, pass_type, topic, source))
        pagination = source.get("pagination")
        if isinstance(pagination, dict):
            template = pagination.get("template")
            if template:
                start = int(pagination.get("start", 1))
                end = int(pagination.get("end", 1))
                step = int(pagination.get("step", 1))
                for page in range(start, end + 1, step):
                    urls.append(
                        template.format(
                            page=page,
                            pass_type=pass_type,
                            topic=quote_plus(topic),
                            **{"pass": pass_type},
                        )
                    )
        rss_url = source.get("rss")
        if rss_url:
            urls.extend(tool.extract_rss_links(rss_url, limit=limit))
        sitemap_url = source.get("sitemap")
        if sitemap_url:
            urls.extend(tool.extract_sitemap_links(sitemap_url, limit=limit))
        deduped = list(dict.fromkeys([url for url in urls if url]))
        return deduped[:limit]

    def _is_recent_enough(self, page: dict[str, Any], source: dict[str, Any]) -> bool:
        strict_recency = bool(source.get("strict_recency"))
        published_at = page.get("published_at")
        if not published_at:
            if strict_recency:
                return False
            return True
        try:
            if isinstance(published_at, str) and published_at.endswith("Z"):
                published_at = published_at[:-1] + "+00:00"
            dt = datetime.fromisoformat(str(published_at))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            return True
        days = int(source.get("recency_days") or self.settings.signal_recency_days)
        if days <= 0:
            return True
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return dt >= cutoff

    def _fetch_reddit_api(self, source: dict[str, Any], pass_type: str, limit: int, topic: str) -> list[dict[str, Any]]:
        cache_root = self.settings.data_dir / "cache" / "signal_engine" / "reddit"
        tool = WebSearchAndSummarize(
            [],
            cache_dir=cache_root,
            timeout=self.settings.request_timeout,
            rate_limit_per_domain=self.settings.rate_limit_per_domain,
            retry_max_attempts=self.settings.retry_max_attempts,
            retry_min_wait=self.settings.retry_min_wait,
            retry_max_wait=self.settings.retry_max_wait,
        )
        url = self._build_pass_url(source.get("url", ""), pass_type, topic, source)
        if "{limit}" in url:
            url = url.format(limit=max(1, limit))
        raw = tool.fetch_url(url, headers={"User-Agent": "Asmblr/1.0 signal-engine"})
        if not raw:
            return []
        try:
            payload = json.loads(raw)
        except Exception:
            return []
        children = (((payload or {}).get("data") or {}).get("children") or [])
        results: list[dict[str, Any]] = []
        for child in children[: max(1, limit)]:
            data = (child or {}).get("data") or {}
            title = str(data.get("title") or "").strip()
            selftext = str(data.get("selftext") or "").strip()
            permalink = data.get("permalink") or ""
            created_utc = data.get("created_utc")
            published_at = None
            if isinstance(created_utc, (int, float)):
                published_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc).isoformat()
            results.append(
                {
                    "url": f"https://www.reddit.com{permalink}" if permalink else source.get("url"),
                    "title": title or source.get("name", "reddit"),
                    "text": f"{title}\n\n{selftext}".strip(),
                    "published_at": published_at,
                    "upvotes": data.get("ups"),
                    "comments_count": data.get("num_comments"),
                }
            )
        return results

    def _fetch_github_issues_api(self, source: dict[str, Any], limit: int, topic: str) -> list[dict[str, Any]]:
        cache_root = self.settings.data_dir / "cache" / "signal_engine" / "github_issues"
        tool = WebSearchAndSummarize(
            [],
            cache_dir=cache_root,
            timeout=self.settings.request_timeout,
            rate_limit_per_domain=self.settings.rate_limit_per_domain,
            retry_max_attempts=self.settings.retry_max_attempts,
            retry_min_wait=self.settings.retry_min_wait,
            retry_max_wait=self.settings.retry_max_wait,
        )
        recency_days = int(source.get("recency_days") or self.settings.signal_recency_days)
        since = (datetime.now(timezone.utc) - timedelta(days=max(1, recency_days))).date().isoformat()
        api_url = str(source.get("api_url") or "").strip()
        if not api_url:
            api_url = (
                "https://api.github.com/search/issues?q="
                "is:issue+state:open+updated:%3E%3D{since}+{topic}&sort=updated&order=desc&per_page={limit}"
            )
        url = api_url.format(
            since=since,
            topic=quote_plus(topic),
            limit=max(1, min(50, limit)),
            pass_type="recent",
        )
        raw = tool.fetch_url(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Asmblr/1.0 signal-engine",
            },
        )
        if not raw:
            return []
        try:
            payload = json.loads(raw)
        except Exception:
            return []
        items = (payload or {}).get("items") or []
        results: list[dict[str, Any]] = []
        for item in items[: max(1, limit)]:
            if not isinstance(item, dict):
                continue
            body = str(item.get("body") or "")
            title = str(item.get("title") or "")
            reactions = item.get("reactions") or {}
            upvotes = None
            if isinstance(reactions, dict):
                upvotes = reactions.get("total_count")
            results.append(
                {
                    "url": item.get("html_url") or source.get("url"),
                    "title": title,
                    "text": f"{title}\n\n{body}".strip(),
                    "published_at": item.get("updated_at") or item.get("created_at"),
                    "upvotes": upvotes,
                    "comments_count": item.get("comments"),
                }
            )
        return results

    def _build_pass_url(
        self, base_url: str, pass_type: str, topic: str, source: dict[str, Any] | None = None
    ) -> str:
        source = source or {}
        templates = source.get("templates") or {}
        if isinstance(templates, dict):
            template = templates.get(pass_type)
            if template:
                return template.format(
                    base_url=base_url,
                    topic=quote_plus(topic),
                    pass_type=pass_type,
                    limit=max(1, int(source.get("limit") or 25)),
                )
        if pass_type == "recent":
            return base_url
        if pass_type == "top":
            return f"{base_url.rstrip('/')}/?sort=top"
        if pass_type == "search":
            return f"https://www.bing.com/search?q=site:{quote_plus(base_url)}+{quote_plus(topic)}"
        return base_url

    def _write_json(self, payload: dict[str, Any], filename: str) -> None:
        path = self.output_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
