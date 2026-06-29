import pytest

from service_security import MissingServiceSecretError, secret_is_authorized


def test_service_auth_fails_closed_without_configured_secret() -> None:
    with pytest.raises(MissingServiceSecretError):
        secret_is_authorized(provided="", configured="")


def test_service_auth_rejects_an_invalid_secret() -> None:
    assert not secret_is_authorized(provided="wrong", configured="expected")


def test_service_auth_accepts_the_configured_secret() -> None:
    assert secret_is_authorized(provided="expected", configured="expected")
