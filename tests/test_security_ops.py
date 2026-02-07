import json
from pathlib import Path

from app.core.audit import write_audit_event
from app.core.config import Settings, previous_secret_allowed, validate_prod_mode


def test_previous_secret_allowed_requires_expiry_when_enforced() -> None:
    allowed, reason = previous_secret_allowed(
        previous_value="old-secret",
        current_value="new-secret",
        expires_at="",
        enforce_rotation=True,
    )
    assert allowed is False
    assert reason == "missing_or_invalid_expiry"


def test_validate_prod_mode_flags_dry_run_and_missing_keys() -> None:
    settings = Settings()
    settings.prod_mode = True
    settings.require_prod_checklist = True
    settings.api_key = ""
    settings.ui_password = ""
    settings.enable_publishing = True
    settings.publish_dry_run = True

    result = validate_prod_mode(settings)
    assert result["ok"] is False
    names = {item["name"] for item in result["checks"] if not item["ok"]}
    assert "api_key_present" in names
    assert "ui_password_present" in names
    assert "publish_dry_run_disabled" in names


def test_audit_redacts_secrets(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.log"
    write_audit_event(
        audit_path,
        {
            "event": "test",
            "api_key": "abcdef123456",
            "nested": {"token": "ghp_abcdef123456"},
            "message": "Authorization: Bearer secret123456",
        },
    )
    line = audit_path.read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["api_key"] != "abcdef123456"
    assert payload["nested"]["token"] != "ghp_abcdef123456"
    assert "secret123456" not in payload["message"]
