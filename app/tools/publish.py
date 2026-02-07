from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PublishConfig:
    linkedin_token: str
    linkedin_author: str
    x_bearer_token: str
    x_user_id: str
    youtube_token: str
    youtube_channel_id: str
    instagram_token: str
    instagram_account_id: str
    dry_run: bool = True
    timeout_s: int = 30


def _post_json(url: str, payload: dict[str, Any], token: str, timeout_s: int) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return {"status": "ok", "text": resp.text}


def publish_linkedin(config: PublishConfig, text: str, media_path: str | None) -> dict[str, Any]:
    payload = {"author": config.linkedin_author, "text": text, "media_path": media_path}
    if config.dry_run:
        return {"dry_run": True, "payload": payload}
    return _post_json("https://api.linkedin.com/v2/ugcPosts", payload, config.linkedin_token, config.timeout_s)


def publish_x(config: PublishConfig, text: str, media_path: str | None) -> dict[str, Any]:
    payload = {"text": text, "media_path": media_path, "user_id": config.x_user_id}
    if config.dry_run:
        return {"dry_run": True, "payload": payload}
    return _post_json("https://api.x.com/2/tweets", payload, config.x_bearer_token, config.timeout_s)


def publish_youtube(config: PublishConfig, title: str, description: str, video_path: str) -> dict[str, Any]:
    payload = {"channel_id": config.youtube_channel_id, "title": title, "description": description, "video_path": video_path}
    if config.dry_run:
        return {"dry_run": True, "payload": payload}
    return _post_json("https://www.googleapis.com/upload/youtube/v3/videos", payload, config.youtube_token, config.timeout_s)


def publish_instagram(config: PublishConfig, caption: str, media_path: str) -> dict[str, Any]:
    payload = {"account_id": config.instagram_account_id, "caption": caption, "media_path": media_path}
    if config.dry_run:
        return {"dry_run": True, "payload": payload}
    return _post_json("https://graph.facebook.com/v19.0/me/media", payload, config.instagram_token, config.timeout_s)
