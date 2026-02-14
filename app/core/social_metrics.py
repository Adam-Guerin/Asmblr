from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import httpx
from loguru import logger

from app.core.config import Settings

METRICOOL_BASE_URL = "https://app.metricool.com/api"


class SocialMetricsAdapter(ABC):
    """Abstract provider for social metric lookups."""

    @abstractmethod
    def fetch(self, run_id: str, posts: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
        raise NotImplementedError


class HttpPostMetricsAdapter(SocialMetricsAdapter):
    def __init__(self, endpoint: str, api_key: str, timeout: float, http_client: httpx.Client | None = None) -> None:
        self.endpoint = endpoint.strip()
        self.api_key = api_key.strip()
        self.timeout = float(timeout)
        self._client = http_client or httpx.Client(timeout=self.timeout)

    def fetch(self, run_id: str, posts: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
        if not self.endpoint or not posts:
            return {}
        payload = {"run_id": run_id, "posts": posts}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        response = self._client.post(
            self.endpoint,
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json() or {}
        return self._normalize_response(body)

    def _normalize_response(self, payload: Any) -> dict[str, list[dict[str, Any]]]:
        if isinstance(payload, dict) and "performance" in payload:
            metrics = payload["performance"] or {}
        else:
            metrics = payload if isinstance(payload, dict) else {}
        result: dict[str, list[dict[str, Any]]] = {}
        for platform, entries in metrics.items():
            if not isinstance(entries, list):
                continue
            normalized_entries: list[dict[str, Any]] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                normalized = dict(entry)
                normalized.setdefault("platform", platform)
                normalized.setdefault("source", normalized.get("source") or "api")
                normalized.setdefault("asset_id", normalized.get("asset_id", ""))
                normalized_entries.append(normalized)
            if normalized_entries:
                result[platform] = normalized_entries
        return result


class MetricoolMetricsAdapter(SocialMetricsAdapter):
    def __init__(
        self,
        base_url: str,
        user_id: str,
        blog_id: str,
        user_token: str,
        timeout: float,
        window_days: int,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else METRICOOL_BASE_URL
        self.user_id = user_id.strip()
        self.blog_id = blog_id.strip()
        self.user_token = user_token.strip()
        self.timeout = float(timeout)
        self.window_days = max(1, int(window_days))
        self._client = http_client or httpx.Client(timeout=self.timeout)

    def fetch(self, run_id: str, posts: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
        if not posts:
            return {}
        entries = self._request_posts(run_id)
        if not entries:
            return {}
        return self._map_posts_to_platforms(posts, entries)

    def _request_posts(self, run_id: str) -> list[dict[str, Any]]:
        if not (self.user_id and self.blog_id and self.user_token):
            logger.warning("Metricool adapter requires user_id, blog_id, and user_token")
            return []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.window_days)
        params = {
            "start": start_date.strftime("%Y%m%d"),
            "end": end_date.strftime("%Y%m%d"),
            "userId": self.user_id,
            "blogId": self.blog_id,
            "userToken": self.user_token,
        }
        url = f"{self.base_url}/stats/posts"
        response = self._client.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            if "posts" in payload and isinstance(payload["posts"], list):
                return payload["posts"]
            return []
        if isinstance(payload, list):
            return payload
        return []

    def _map_posts_to_platforms(
        self, posts: dict[str, list[dict[str, Any]]], metrics: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        remaining = list(metrics)
        results: dict[str, list[dict[str, Any]]] = {}
        for platform, variants in posts.items():
            platform_entries: list[dict[str, Any]] = []
            for variant in variants or []:
                matched = self._match_variant(variant, remaining)
                platform_entries.append(self._build_entry(platform, variant, matched))
            if platform_entries:
                results[platform] = platform_entries
        return results

    def _match_variant(
        self, variant: dict[str, Any], candidates: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        final_url = (variant.get("final_url") or "").strip().rstrip("/").lower()
        text = (variant.get("text") or "").strip().lower()
        best_index: int | None = None
        for index, item in enumerate(candidates):
            if not isinstance(item, dict):
                continue
            post_url = (item.get("postUrl") or "").strip().rstrip("/").lower()
            title = (item.get("title") or "").strip().lower()
            excerpt = (item.get("excerpt") or "").strip().lower()
            if final_url and post_url and final_url == post_url:
                best_index = index
                break
            if text and title and text in title:
                best_index = index
                break
            if text and excerpt and text in excerpt:
                best_index = index
                break
            if text and title:
                text_tokens = set(text.split())
                title_tokens = set(title.split())
                if text_tokens and title_tokens:
                    overlap = len(text_tokens & title_tokens)
                    threshold = max(1, len(text_tokens) // 4)
                    if overlap >= threshold:
                        best_index = index
                        break
        if best_index is not None:
            return candidates.pop(best_index)
        return None

    def _build_entry(
        self, platform: str, variant: dict[str, Any], payload: dict[str, Any] | None
    ) -> dict[str, Any]:
        entry = {
            "platform": platform,
            "asset_id": variant.get("asset_id", ""),
            "source": "metricool",
            "final_url": variant.get("final_url"),
            "text": variant.get("text"),
            "created_at": variant.get("created_at"),
        }
        if not payload:
            entry.update({"score": 0.0, "ctr": 0.0, "engagement_rate": 0.0, "impressions": 0, "clicks": 0})
            return entry
        impressions = self._to_int(payload.get("pageViews") or payload.get("totalPageViews"))
        clicks = self._to_int(payload.get("totalShares"))
        comments = self._to_int(payload.get("commentsCount"))
        likes = sum(
            self._to_int(payload.get(field)) for field in ("fbShares", "twShares", "inShares", "pinShares")
        )
        engagements = comments + likes + self._to_int(payload.get("totalShares"))
        ctr = round(clicks / max(impressions, 1), 4)
        engagement_rate = round(min(1.0, engagements / max(impressions, 1)), 4)
        score = round(ctr * 0.7 + engagement_rate * 0.3, 4)
        entry.update(
            {
                "impressions": impressions,
                "clicks": clicks,
                "comments": comments,
                "likes": likes,
                "ctr": ctr,
                "engagement_rate": engagement_rate,
                "score": score,
                "metricool_post_url": payload.get("postUrl"),
            }
        )
        _apply_variant_metadata(entry, variant)
        entry.setdefault("reported_at", datetime.utcnow().isoformat())
        return entry

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0


def build_social_metrics_adapter(settings: Settings) -> SocialMetricsAdapter | None:
    provider = (settings.social_metrics_provider or "").strip().lower()
    if provider == "metricool":
        if not (settings.social_metrics_user_id and settings.social_metrics_blog_id and settings.social_metrics_token):
            logger.warning("Metricool metrics adapter disabled because credentials are incomplete.")
            return None
        return MetricoolMetricsAdapter(
            base_url=settings.social_metrics_api_url or METRICOOL_BASE_URL,
            user_id=settings.social_metrics_user_id,
            blog_id=settings.social_metrics_blog_id,
            user_token=settings.social_metrics_token,
            timeout=settings.social_metrics_timeout_s,
            window_days=settings.social_metrics_window_days,
        )
    if settings.social_metrics_api_url:
        return HttpPostMetricsAdapter(
            endpoint=settings.social_metrics_api_url,
            api_key=settings.social_metrics_api_key,
            timeout=settings.social_metrics_timeout_s,
        )
    return None


def _infer_content_format(variant: dict[str, Any]) -> str:
    if not isinstance(variant, dict):
        return "text"
    if variant.get("video_title") or variant.get("voiceover") or variant.get("storyboard"):
        return "video"
    if variant.get("image_path") or variant.get("image_title") or variant.get("image_subtitle"):
        return "image"
    return "text"


def _variant_metadata(variant: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(variant, dict):
        return {
            "final_url": None,
            "cta": None,
            "hashtags": [],
            "variant_text": None,
            "content_format": "text",
            "published_at": None,
        }
    return {
        "final_url": variant.get("final_url"),
        "cta": variant.get("cta"),
        "hashtags": [str(tag) for tag in (variant.get("hashtags") or []) if str(tag).strip()],
        "variant_text": variant.get("text"),
        "content_format": variant.get("content_format") or _infer_content_format(variant),
        "published_at": variant.get("created_at"),
    }


def _apply_variant_metadata(entry: dict[str, Any], variant: dict[str, Any]) -> None:
    meta = _variant_metadata(variant)
    if meta["final_url"]:
        entry["final_url"] = meta["final_url"]
    if meta["cta"]:
        entry["cta"] = meta["cta"]
    entry["hashtags"] = meta["hashtags"]
    entry["variant_text"] = meta["variant_text"]
    entry["content_format"] = meta["content_format"]
    if meta["published_at"]:
        entry["published_at"] = meta["published_at"]
