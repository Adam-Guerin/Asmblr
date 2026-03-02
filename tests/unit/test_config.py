from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core import config as config_module
from app.core.config import (
    Settings,
    _mask_secret,
    _parse_iso_datetime,
    get_settings,
    previous_secret_allowed,
    redact_value,
    validate_prod_mode,
    validate_secrets,
)


@pytest.fixture(autouse=True)
def _disable_lightweight_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        config_module.lightweight_config,
        "apply_ai_optimizations",
        lambda *_args, **_kwargs: None,
    )


def test_parse_iso_datetime_accepts_valid_values() -> None:
    parsed = _parse_iso_datetime("2026-03-01T10:00:00")
    assert parsed is not None
    assert parsed.tzinfo == UTC

    parsed_z = _parse_iso_datetime("2026-03-01T10:00:00Z")
    assert parsed_z is not None

    parsed_compact = _parse_iso_datetime("20260301T100000")
    assert parsed_compact is not None


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "not-a-date",
        "2026-13-99T77:00:00",
        "1900-01-01T00:00:00",
        "9999-01-01T00:00:00",
    ],
)
def test_parse_iso_datetime_rejects_invalid_values(value: str | None) -> None:
    assert _parse_iso_datetime(value) is None


def test_previous_secret_allowed_paths() -> None:
    allowed, reason = previous_secret_allowed(
        previous_value="",
        current_value="new",
        expires_at="2026-12-01T00:00:00",
        enforce_rotation=True,
    )
    assert (allowed, reason) == (False, "not_configured")

    allowed, reason = previous_secret_allowed(
        previous_value="same",
        current_value="same",
        expires_at="2026-12-01T00:00:00",
        enforce_rotation=True,
    )
    assert (allowed, reason) == (False, "same_as_current")

    allowed, reason = previous_secret_allowed(
        previous_value="legacy",
        current_value="current",
        expires_at="bad-expiry",
        enforce_rotation=False,
    )
    assert (allowed, reason) == (True, "allowed_legacy")


def test_previous_secret_allowed_expiry_paths() -> None:
    expired = (datetime.now(UTC) - timedelta(days=1)).replace(microsecond=0).isoformat()
    future = (datetime.now(UTC) + timedelta(days=1)).replace(microsecond=0).isoformat()

    allowed, reason = previous_secret_allowed(
        previous_value="prev",
        current_value="cur",
        expires_at=expired,
        enforce_rotation=True,
    )
    assert (allowed, reason) == (False, "expired")

    allowed, reason = previous_secret_allowed(
        previous_value="prev",
        current_value="cur",
        expires_at=future,
        enforce_rotation=True,
    )
    assert (allowed, reason) == (True, "within_grace_period")


def test_mask_secret_and_redact_nested_structures() -> None:
    assert _mask_secret("") == "***"
    assert _mask_secret("abcde") == "***"
    assert _mask_secret("abcdefgh") == "ab***gh"

    payload = {
        "api_key": "abcdefgh1234",
        "nested": [{"token": "secrettoken"}, ("keep", {"password": "passcode"})],
    }
    redacted = redact_value(payload)
    assert redacted["api_key"].startswith("ab***")
    assert redacted["nested"][0]["token"] == "se***en"
    assert redacted["nested"][1][1]["password"] == "pa***de"


def test_redact_value_on_strings() -> None:
    text = "api_key=abcdef123456 and bearer abcdef123456"
    redacted = redact_value(text)
    assert "abcdef123456" not in redacted
    assert "api_key=ab***56" in redacted.lower()


def test_get_settings_validates_numeric_constraints(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BadSettings:
        run_max_count = 0
        run_retention_days = 30
        kill_threshold = 55
        mvp_build_timeout = 300
        mvp_test_timeout = 300
        mvp_install_timeout = 600
        run_rate_limit_per_min = 6
        run_rate_limit_burst = 3

    monkeypatch.setattr(config_module, "Settings", _BadSettings)
    with pytest.raises(ValueError, match="RUN_MAX_COUNT"):
        get_settings()


def test_validate_secrets_with_enabled_services(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTWEIGHT_MODE", "false")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "")
    monkeypatch.setenv("AWS_REGION", "")

    settings = Settings(
        enable_publishing=True,
        publish_dry_run=False,
        enable_ads=True,
        ads_dry_run=False,
        enable_hosting=True,
        hosting_provider="aws_apprunner",
    )
    result = validate_secrets(settings)
    assert result["ok"] is False
    enabled_checks = [c for c in result["checks"] if c["enabled"]]
    assert enabled_checks
    assert any(c["missing"] for c in enabled_checks)


def test_validate_prod_mode_when_not_prod() -> None:
    settings = Settings(prod_mode=False)
    result = validate_prod_mode(settings)
    assert result["ok"] is True
    assert result["checks"][0]["name"] == "prod_mode"


def test_validate_prod_mode_flags_missing_requirements(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTWEIGHT_MODE", "false")
    settings = Settings(
        prod_mode=True,
        api_key="",
        ui_password="",
        enable_publishing=True,
        publish_dry_run=True,
        enable_ads=True,
        ads_dry_run=True,
        enable_deploy=True,
        deploy_dry_run=True,
        enable_hosting=False,
    )
    result = validate_prod_mode(settings)
    assert result["ok"] is False
    names = {c["name"] for c in result["checks"]}
    assert "api_key_present" in names
    assert "ui_password_present" in names
    assert "publish_dry_run_disabled" in names
    assert "ads_dry_run_disabled" in names
    assert "deploy_dry_run_disabled" in names
