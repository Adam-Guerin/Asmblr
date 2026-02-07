from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class AdsConfig:
    google_customer_id: str
    google_dev_token: str
    google_client_id: str
    google_client_secret: str
    google_refresh_token: str
    meta_access_token: str
    meta_ad_account_id: str
    tiktok_access_token: str
    tiktok_ad_account_id: str
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


def create_google_ads_campaign(config: AdsConfig, payload: dict[str, Any]) -> dict[str, Any]:
    if config.dry_run:
        return {"dry_run": True, "payload": payload}
    url = f"https://googleads.googleapis.com/v16/customers/{config.google_customer_id}/googleAds:mutate"
    return _post_json(url, payload, config.google_dev_token, config.timeout_s)


def create_meta_ads_campaign(config: AdsConfig, payload: dict[str, Any]) -> dict[str, Any]:
    if config.dry_run:
        return {"dry_run": True, "payload": payload}
    url = f"https://graph.facebook.com/v19.0/act_{config.meta_ad_account_id}/campaigns"
    return _post_json(url, payload, config.meta_access_token, config.timeout_s)


def create_tiktok_ads_campaign(config: AdsConfig, payload: dict[str, Any]) -> dict[str, Any]:
    if config.dry_run:
        return {"dry_run": True, "payload": payload}
    url = "https://business-api.tiktok.com/open_api/v1.3/campaign/create/"
    return _post_json(url, payload, config.tiktok_access_token, config.timeout_s)
