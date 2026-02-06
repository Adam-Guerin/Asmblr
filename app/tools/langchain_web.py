"""LangChain tools for web fetching and competitor extraction."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from langchain.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, conint, validator

from app.core.constants import DEFAULT_CACHE_DIR
from app.tools.competitor import extract_competitors
from app.tools.web import WebSearchAndSummarize, WebSource


def is_valid_url(url: str) -> bool:
    """Return True if the URL is http(s) with a netloc."""
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


class WebSearchArgs(BaseModel):
    """Arguments for web_search_and_summarize tool."""

    sources: List[Dict[str, str]]
    max_sources: conint(ge=1, le=50) = 8
    cache_dir: str
    timeout: conint(ge=5, le=60) = 20
    rate_limit_per_domain: conint(ge=1, le=10) = 2
    retry_max_attempts: conint(ge=1, le=6) = 3
    retry_min_wait: conint(ge=1, le=10) = 1
    retry_max_wait: conint(ge=1, le=30) = 6

    @validator("sources")
    def validate_sources(cls, value: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not value:
            raise ValueError("sources must not be empty")
        cleaned: List[Dict[str, str]] = []
        for entry in value:
            name = (entry or {}).get("name", "").strip()
            url = (entry or {}).get("url", "").strip()
            if not name or not is_valid_url(url):
                raise ValueError(f"invalid source entry: {entry}")
            cleaned.append({"name": name, "url": url})
        return cleaned


class WebSearchAndSummarizeTool(BaseTool):
    """Scrape configured sources and summarize pages into JSON."""

    name: str = "web_search_and_summarize"
    description: str = "Scrape configured sources (respect robots.txt) and summarize HTML pages. Returns JSON list of pages."
    args_schema: type[BaseModel] = WebSearchArgs

    def _run(
        self,
        sources: List[Dict[str, str]],
        max_sources: int,
        cache_dir: str,
        timeout: int,
        rate_limit_per_domain: int,
        retry_max_attempts: int = 3,
        retry_min_wait: int = 1,
        retry_max_wait: int = 6,
    ) -> str:
        """Execute the web search and return a JSON payload of pages."""
        try:
            web_sources = [WebSource(name=s["name"], url=s["url"]) for s in sources]
            tool = WebSearchAndSummarize(
                web_sources,
                cache_dir=Path(cache_dir),
                timeout=timeout,
                rate_limit_per_domain=rate_limit_per_domain,
                retry_max_attempts=retry_max_attempts,
                retry_min_wait=retry_min_wait,
                retry_max_wait=retry_max_wait,
            )
            pages = tool.run(max_sources=max_sources)
        except Exception as exc:
            logger.warning("web_search_and_summarize failed: {err}", err=exc)
            pages = []
        return json.dumps(pages, indent=2)


class CompetitorArgs(BaseModel):
    """Arguments for competitor_extractor tool."""

    pages: Optional[List[Dict[str, Any]]] = None
    urls: Optional[List[str]] = None
    cache_dir: Optional[str] = None
    timeout: conint(ge=5, le=60) = 20
    rate_limit_per_domain: conint(ge=1, le=10) = 2
    retry_max_attempts: conint(ge=1, le=6) = 3
    retry_min_wait: conint(ge=1, le=10) = 1
    retry_max_wait: conint(ge=1, le=30) = 6

    @validator("urls")
    def validate_urls(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return value
        cleaned = [u.strip() for u in value if u and u.strip()]
        if not cleaned:
            raise ValueError("urls provided but empty")
        for url in cleaned:
            if not is_valid_url(url):
                raise ValueError(f"invalid url: {url}")
        return cleaned


class CompetitorExtractorTool(BaseTool):
    """Extract competitors, pricing, and positioning from pages."""

    name: str = "competitor_extractor"
    description: str = "Extract competitors, pricing, and positioning from HTML pages. Returns JSON list."
    args_schema: type[BaseModel] = CompetitorArgs

    def _run(
        self,
        pages: Optional[List[Dict[str, Any]]] = None,
        urls: Optional[List[str]] = None,
        cache_dir: Optional[str] = None,
        timeout: int = 20,
        rate_limit_per_domain: int = 2,
        retry_max_attempts: int = 3,
        retry_min_wait: int = 1,
        retry_max_wait: int = 6,
    ) -> str:
        """Execute competitor extraction and return JSON payload."""
        page_list = pages or []
        try:
            if urls:
                cache_path = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
                web_sources = [WebSource(name=f"competitor-{idx+1}", url=u) for idx, u in enumerate(urls)]
                web = WebSearchAndSummarize(
                    web_sources,
                    cache_dir=cache_path,
                    timeout=timeout,
                    rate_limit_per_domain=rate_limit_per_domain,
                    retry_max_attempts=retry_max_attempts,
                    retry_min_wait=retry_min_wait,
                    retry_max_wait=retry_max_wait,
                )
                page_list = web.run(max_sources=len(urls))
            competitors = extract_competitors(page_list)
        except Exception as exc:
            logger.warning("competitor_extractor failed: {err}", err=exc)
            competitors = []
        return json.dumps(competitors, indent=2)
