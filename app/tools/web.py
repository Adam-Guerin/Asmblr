import hashlib
import json
import time
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random
import ipaddress
from typing import Any
from urllib.parse import urlparse, quote_plus
from urllib.robotparser import RobotFileParser

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from bs4 import BeautifulSoup
from loguru import logger

from app.core.constants import (
    WEB_MIN_TIMEOUT_S,
    WEB_MAX_TIMEOUT_S,
    WEB_CONNECT_TIMEOUT_S,
    WEB_WRITE_TIMEOUT_S,
    WEB_POOL_TIMEOUT_S,
    WEB_USER_AGENT,
    WEB_MAX_WORKERS,
    WEB_RATE_MIN,
    WEB_TOKEN_BUCKET_MULTIPLIER,
    WEB_JITTER_MIN,
    WEB_JITTER_MAX,
)

@dataclass
class WebSource:
    name: str
    url: str


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.status_code >= 500 or resp.status_code == 429:
        raise httpx.HTTPStatusError("retryable status", request=resp.request, response=resp)
    if hasattr(resp, "raise_for_status"):
        resp.raise_for_status()


class WebSearchAndSummarize:
    def __init__(
        self,
        sources: list[WebSource],
        cache_dir: Path,
        timeout: int = 20,
        rate_limit_per_domain: int = 2,
        retry_max_attempts: int = 3,
        retry_min_wait: int = 1,
        retry_max_wait: int = 6,
    ) -> None:
        self.sources = sources
        self.cache_dir = cache_dir
        self.timeout = timeout
        self.rate_limit_per_domain = rate_limit_per_domain
        self.retry_max_attempts = retry_max_attempts
        self.retry_min_wait = retry_min_wait
        self.retry_max_wait = retry_max_wait
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning("Failed to create cache dir {dir}: {err}", dir=self.cache_dir, err=exc)
        self._last_request: dict[str, float] = {}
        self._robots_cache: dict[str, RobotFileParser] = {}
        self._lock = threading.Lock()
        self._timeout_config = self._normalize_timeout(self.timeout)
        self._rate_state: dict[str, dict[str, float]] = {}

    def _normalize_timeout(self, timeout: int) -> httpx.Timeout:
        if not isinstance(timeout, int) or timeout <= 0:
            timeout = 20
        timeout = max(WEB_MIN_TIMEOUT_S, min(timeout, WEB_MAX_TIMEOUT_S))
        return httpx.Timeout(
            timeout,
            connect=WEB_CONNECT_TIMEOUT_S,
            read=float(timeout),
            write=WEB_WRITE_TIMEOUT_S,
            pool=WEB_POOL_TIMEOUT_S,
        )

    def _is_valid_url(self, url: str) -> bool:
        if not url or not isinstance(url, str):
            return False
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        host = parsed.hostname or ""
        if host in {"localhost"}:
            return False
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            pass
        return True

    def _cache_path(self, url: str) -> Path:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{key}.json"

    def _get_robot(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base in self._robots_cache:
            return self._robots_cache[base]
        robots_url = f"{base}/robots.txt"
        rp = RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
        except Exception:
            rp = RobotFileParser()
            rp.parse("User-agent: *\nDisallow:".splitlines())
        self._robots_cache[base] = rp
        return rp

    def _is_allowed(self, url: str) -> bool:
        rp = self._get_robot(url)
        return rp.can_fetch("*", url)

    def _rate_limit(self, url: str) -> None:
        domain = urlparse(url).netloc
        now = time.time()
        rate = max(WEB_RATE_MIN, float(self.rate_limit_per_domain))
        refill = rate
        capacity = max(1.0, rate * WEB_TOKEN_BUCKET_MULTIPLIER)
        with self._lock:
            state = self._rate_state.get(domain)
            if not state:
                state = {"tokens": capacity, "last": now}
                self._rate_state[domain] = state
            elapsed = now - state["last"]
            state["tokens"] = min(capacity, state["tokens"] + elapsed * refill)
            state["last"] = now
            if state["tokens"] < 1.0:
                wait_for = (1.0 - state["tokens"]) / refill
                jitter = random.uniform(WEB_JITTER_MIN, WEB_JITTER_MAX)
                time.sleep(wait_for + jitter)
                state["tokens"] = 0.0
            else:
                state["tokens"] -= 1.0
            self._last_request[domain] = time.time()
            logger.debug("rate_limit domain={domain} tokens={tokens:.2f}", domain=domain, tokens=state["tokens"])

    def fetch(self, url: str) -> str:
        if not self._is_valid_url(url):
            logger.warning("Invalid URL skipped: {url}", url=url)
            return ""
        cache_path = self._cache_path(url)
        if cache_path.exists():
            try:
                logger.debug("cache_hit url={url}", url=url)
                return json.loads(cache_path.read_text(encoding="utf-8")).get("text", "")
            except Exception:
                return ""
        if not self._is_allowed(url):
            logger.warning("Blocked by robots.txt: {url}", url=url)
            return ""
        self._rate_limit(url)
        headers = {"User-Agent": WEB_USER_AGENT}
        text = self.fetch_url(url, headers=headers)
        cache_path.write_text(json.dumps({"url": url, "text": text}), encoding="utf-8")
        return text

    def fetch_url(self, url: str, headers: dict[str, str] | None = None) -> str:
        @retry(
            stop=stop_after_attempt(self.retry_max_attempts),
            wait=wait_exponential(min=self.retry_min_wait, max=self.retry_max_wait),
            retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
            reraise=True,
        )
        def _do_fetch() -> str:
            self._rate_limit(url)
            start = time.time()
            with httpx.Client(
                timeout=self._timeout_config,
                headers=headers,
                follow_redirects=True,
            ) as client:
                resp = client.get(url)
                _raise_for_status(resp)
                elapsed = time.time() - start
                logger.info("web_fetch ok url={url} status={status} time={time:.2f}s", url=url, status=resp.status_code, time=elapsed)
                return resp.text

        try:
            return _do_fetch()
        except Exception as exc:
            logger.warning("web_fetch failed url={url} error={err}", url=url, err=exc)
            return ""

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()
        main = soup.find("main") or soup.find("article")
        target = main if main else soup.body or soup
        text = " ".join(target.stripped_strings)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def detect_language(self, text: str) -> str:
        if not text:
            return "unknown"
        sample = text.lower()[:2000]
        tokens = re.findall(r"\b[a-zàâçéèêëîïôûùüÿñæœ]+\b", sample)
        if not tokens:
            return "unknown"
        en_stop = {"the","and","to","of","in","for","is","on","that","with","as","it","are","this","be","or"}
        fr_stop = {"le","la","les","et","des","pour","est","dans","une","que","qui","sur","pas","plus","par","au"}
        en_hits = sum(1 for t in tokens if t in en_stop)
        fr_hits = sum(1 for t in tokens if t in fr_stop)
        if en_hits == 0 and fr_hits == 0:
            return "unknown"
        return "fr" if fr_hits > en_hits else "en"

    def extract_engagement(self, html: str) -> dict:
        if not html:
            return {"upvotes": None, "comments_count": None}
        soup = BeautifulSoup(html, "html.parser")
        text = " ".join(soup.stripped_strings)
        lowered = text.lower()
        upvotes = None
        comments = None

        # Common structured hints (Reddit, HN, Product Hunt, etc.)
        for attr in ("data-score", "data-upvotes", "data-upvote-count", "data-vote-count"):
            tag = soup.find(attrs={attr: True})
            if tag:
                try:
                    upvotes = int(tag.get(attr))
                    break
                except Exception:
                    pass

        # Look for "points"/"upvotes" patterns
        if upvotes is None:
            match = re.search(r"(\d{1,6})\s+(points|upvotes)", lowered)
            if match:
                try:
                    upvotes = int(match.group(1))
                except Exception:
                    pass

        # Comments count patterns
        match = re.search(r"(\d{1,6})\s+(comments|comment)", lowered)
        if match:
            try:
                comments = int(match.group(1))
            except Exception:
                pass

        # HN specific: "X points" and "Y comments"
        if upvotes is None:
            match = re.search(r"(\d{1,6})\s+points", lowered)
            if match:
                try:
                    upvotes = int(match.group(1))
                except Exception:
                    pass

        return {"upvotes": upvotes, "comments_count": comments}

    def extract_published_at(self, html: str) -> str | None:
        if not html:
            return None
        soup = BeautifulSoup(html, "html.parser")
        for tag_name in ("relative-time", "time"):
            for time_tag in soup.find_all(tag_name):
                candidate = time_tag.get("datetime") or time_tag.get("title") or time_tag.get_text(strip=True)
                if candidate:
                    parsed = self._parse_datetime(str(candidate))
                    if parsed:
                        return parsed
        meta_keys = [
            ("property", "article:published_time"),
            ("property", "og:published_time"),
            ("name", "pubdate"),
            ("name", "publishdate"),
            ("name", "publish-date"),
            ("name", "date"),
            ("name", "datePublished"),
            ("name", "sailthru.date"),
            ("itemprop", "datePublished"),
        ]
        for attr, value in meta_keys:
            tag = soup.find("meta", attrs={attr: value})
            if tag and tag.get("content"):
                parsed = self._parse_datetime(tag["content"])
                if parsed:
                    return parsed
        for tag in soup.find_all("meta"):
            if tag.get("name") in {"publishdate", "pubdate", "date"} and tag.get("content"):
                parsed = self._parse_datetime(tag["content"])
                if parsed:
                    return parsed
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                payload = json.loads(script.get_text() or "{}")
            except Exception:
                continue
            candidates = []
            if isinstance(payload, list):
                candidates.extend(payload)
            elif isinstance(payload, dict):
                candidates.append(payload)
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                for key in ("datePublished", "dateCreated", "dateModified"):
                    if item.get(key):
                        parsed = self._parse_datetime(str(item[key]))
                        if parsed:
                            return parsed
        return None

    def _parse_datetime(self, value: str) -> str | None:
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
            pass
        try:
            dt = parsedate_to_datetime(text)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            pass
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                continue
        return None

    def summarize(self, text: str, max_sentences: int = 5) -> str:
        sentences = text.split(".")
        summary = ". ".join([s.strip() for s in sentences if s.strip()][:max_sentences])
        return summary

    def run(self, max_sources: int = 8) -> list[dict[str, Any]]:
        sources = [s for s in self.sources[:max_sources] if s.url and self._is_valid_url(s.url)]
        results: list[dict[str, Any]] = []
        if not sources:
            return results
        max_workers = min(WEB_MAX_WORKERS, len(sources))
        logger.debug("web_run sources=%d workers=%d", len(sources), max_workers)

        def _work(source: WebSource) -> dict[str, Any] | None:
            try:
                html = self.fetch(source.url)
                if not html:
                    return None
                text = self.extract_text(html)
                summary = self.summarize(text)
                published_at = self.extract_published_at(html)
                language = self.detect_language(text)
                engagement = self.extract_engagement(html)
                return {
                    "name": source.name,
                    "url": source.url,
                    "summary": summary,
                    "text": text,
                    "published_at": published_at,
                    "language": language,
                    "upvotes": engagement.get("upvotes"),
                    "comments_count": engagement.get("comments_count"),
                }
            except Exception as exc:
                logger.warning("web_source failed name={name} url={url} error={err}", name=source.name, url=source.url, err=exc)
                return None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_work, source) for source in sources]
            for future in as_completed(futures):
                item = future.result()
                if item:
                    results.append(item)
        return results

    def search_bing(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not query:
            return []
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        html = self.fetch_url(search_url, headers={"User-Agent": WEB_USER_AGENT})
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        links: list[str] = []
        for item in soup.select("li.b_algo h2 a"):
            href = item.get("href")
            if not href or not self._is_valid_url(href):
                continue
            if href not in links:
                links.append(href)
            if len(links) >= limit:
                break
        results: list[dict[str, Any]] = []
        for url in links:
            try:
                page_html = self.fetch(url)
                if not page_html:
                    continue
                text = self.extract_text(page_html)
                summary = self.summarize(text)
                published_at = self.extract_published_at(page_html)
                language = self.detect_language(text)
                engagement = self.extract_engagement(page_html)
                results.append(
                    {
                        "name": "bing",
                        "url": url,
                        "summary": summary,
                        "text": text,
                        "published_at": published_at,
                        "language": language,
                        "upvotes": engagement.get("upvotes"),
                        "comments_count": engagement.get("comments_count"),
                    }
                )
            except Exception as exc:
                logger.warning("bing_result failed url={url} error={err}", url=url, err=exc)
        return results

    def extract_rss_links(self, rss_url: str, limit: int = 20) -> list[str]:
        if not rss_url:
            return []
        try:
            xml_text = self.fetch_url(rss_url, headers={"User-Agent": WEB_USER_AGENT})
            if not xml_text:
                return []
            soup = BeautifulSoup(xml_text, "xml")
            links: list[str] = []
            for item in soup.find_all("item"):
                link = item.find("link")
                if link and link.text:
                    url = link.text.strip()
                    if self._is_valid_url(url) and url not in links:
                        links.append(url)
            for entry in soup.find_all("entry"):
                link = entry.find("link")
                href = link.get("href") if link else None
                if href and self._is_valid_url(href) and href not in links:
                    links.append(href)
            return links[:limit]
        except Exception as exc:
            logger.warning("rss parse failed url={url} error={err}", url=rss_url, err=exc)
            return []

    def extract_sitemap_links(self, sitemap_url: str, limit: int = 50) -> list[str]:
        if not sitemap_url:
            return []
        try:
            xml_text = self.fetch_url(sitemap_url, headers={"User-Agent": WEB_USER_AGENT})
            if not xml_text:
                return []
            soup = BeautifulSoup(xml_text, "xml")
            links: list[str] = []
            sitemap_locs = [loc.text.strip() for loc in soup.find_all("loc") if loc and loc.text]
            # If this is a sitemap index, fetch nested sitemaps.
            if soup.find("sitemapindex"):
                for loc in sitemap_locs:
                    if not self._is_valid_url(loc):
                        continue
                    links.extend(self.extract_sitemap_links(loc, limit=limit))
                    if len(links) >= limit:
                        break
                return list(dict.fromkeys(links))[:limit]
            # Otherwise treat as urlset.
            for loc in sitemap_locs:
                if self._is_valid_url(loc) and loc not in links:
                    links.append(loc)
                if len(links) >= limit:
                    break
            return links
        except Exception as exc:
            logger.warning("sitemap parse failed url={url} error={err}", url=sitemap_url, err=exc)
            return []
