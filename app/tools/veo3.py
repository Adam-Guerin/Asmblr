from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict

import httpx


@dataclass
class Veo3Config:
    base_url: str
    api_key: str
    timeout_s: int = 120
    poll_interval_s: int = 5
    submit_path: str = "/generate"
    status_path: str = "/status/{job_id}"
    download_path: str = "/download/{job_id}"


def _auth_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}"}


def submit_video_job(config: Veo3Config, payload: Dict[str, Any]) -> str:
    url = config.base_url.rstrip("/") + config.submit_path
    with httpx.Client(timeout=config.timeout_s) as client:
        resp = client.post(url, json=payload, headers=_auth_headers(config.api_key))
        resp.raise_for_status()
        data = resp.json()
    job_id = data.get("job_id") or data.get("id")
    if not job_id:
        raise RuntimeError("Veo3: missing job_id in response")
    return str(job_id)


def wait_for_video_job(config: Veo3Config, job_id: str) -> Dict[str, Any]:
    url = config.base_url.rstrip("/") + config.status_path.format(job_id=job_id)
    deadline = time.time() + config.timeout_s
    with httpx.Client(timeout=config.timeout_s) as client:
        while time.time() < deadline:
            resp = client.get(url, headers=_auth_headers(config.api_key))
            resp.raise_for_status()
            data = resp.json()
            status = str(data.get("status") or "").lower()
            if status in {"completed", "succeeded", "done"}:
                return data
            if status in {"failed", "error"}:
                raise RuntimeError(f"Veo3: job failed: {data}")
            time.sleep(config.poll_interval_s)
    raise RuntimeError("Veo3: job timeout")


def download_video(config: Veo3Config, job_id: str) -> bytes:
    url = config.base_url.rstrip("/") + config.download_path.format(job_id=job_id)
    with httpx.Client(timeout=config.timeout_s) as client:
        resp = client.get(url, headers=_auth_headers(config.api_key))
        resp.raise_for_status()
        return resp.content
