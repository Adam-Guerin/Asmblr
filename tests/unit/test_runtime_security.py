import socket

import pytest

from app.core.runtime_security import (
    ApiKeyConfigurationError,
    InvalidWebhookUrlError,
    api_key_is_authorized,
    validate_webhook_url,
)


def test_api_key_is_authorized_fails_closed_when_key_is_not_configured() -> None:
    with pytest.raises(ApiKeyConfigurationError):
        api_key_is_authorized(provided="", current="")


def test_api_key_is_authorized_accepts_the_current_key() -> None:
    assert api_key_is_authorized(provided="current-secret", current="current-secret")


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/hook",
        "http://[::1]/hook",
        "http://169.254.169.254/latest/meta-data",
        "file:///etc/passwd",
        "https://user:password@example.com/hook",
    ],
)
def test_validate_webhook_url_rejects_unsafe_targets(url: str) -> None:
    with pytest.raises(InvalidWebhookUrlError):
        validate_webhook_url(url)


def test_validate_webhook_url_rejects_hostname_resolving_to_private_ip() -> None:
    def private_resolver(*_args, **_kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]

    with pytest.raises(InvalidWebhookUrlError):
        validate_webhook_url("https://hooks.example.com/events", resolver=private_resolver)


def test_validate_webhook_url_accepts_public_https_target() -> None:
    def public_resolver(*_args, **_kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    assert (
        validate_webhook_url(
            "https://hooks.example.com/events", resolver=public_resolver
        )
        == "https://hooks.example.com/events"
    )
