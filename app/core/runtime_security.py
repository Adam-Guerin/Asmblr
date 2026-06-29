from __future__ import annotations

import hmac
import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urlsplit, urlunsplit

import httpx


class ApiKeyConfigurationError(RuntimeError):
    pass


class InvalidWebhookUrlError(ValueError):
    pass


Resolver = Callable[..., list[tuple]]


def api_key_is_authorized(*, provided: str, current: str) -> bool:
    if not current:
        raise ApiKeyConfigurationError("API_KEY is not configured")
    return bool(provided) and hmac.compare_digest(provided, current)


def secrets_match(provided: str, expected: str) -> bool:
    return bool(provided and expected) and hmac.compare_digest(provided, expected)


def _resolved_addresses(hostname: str, port: int, resolver: Resolver) -> set[str]:
    try:
        records = resolver(hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise InvalidWebhookUrlError("Webhook host could not be resolved") from exc
    addresses = {record[4][0].split("%", 1)[0] for record in records}
    if not addresses:
        raise InvalidWebhookUrlError("Webhook host did not resolve to an address")
    return addresses


def validate_webhook_url(url: str, *, resolver: Resolver = socket.getaddrinfo) -> str:
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise InvalidWebhookUrlError("Webhook URL is malformed") from exc

    if parsed.scheme not in {"http", "https"}:
        raise InvalidWebhookUrlError("Webhook URL must use http or https")
    if not parsed.hostname:
        raise InvalidWebhookUrlError("Webhook URL must include a host")
    if parsed.username is not None or parsed.password is not None:
        raise InvalidWebhookUrlError("Webhook URL must not include credentials")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise InvalidWebhookUrlError("Webhook URL must not target localhost")

    target_port = port or (443 if parsed.scheme == "https" else 80)
    for address in _resolved_addresses(hostname, target_port, resolver):
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise InvalidWebhookUrlError("Webhook host resolved to an invalid address") from exc
        if not ip.is_global:
            raise InvalidWebhookUrlError("Webhook URL must resolve only to public addresses")

    return urlunsplit(parsed)


def post_webhook(url: str, payload: dict, *, timeout_seconds: float = 5.0) -> bool:
    try:
        safe_url = validate_webhook_url(url)
        timeout = httpx.Timeout(
            timeout_seconds,
            connect=min(3.0, timeout_seconds),
            read=timeout_seconds,
            write=timeout_seconds,
            pool=min(3.0, timeout_seconds),
        )
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            response = client.post(safe_url, json=payload)
            response.raise_for_status()
        return True
    except (InvalidWebhookUrlError, httpx.HTTPError):
        return False
