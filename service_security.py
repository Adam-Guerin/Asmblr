from __future__ import annotations

import hmac


class MissingServiceSecretError(RuntimeError):
    pass


def secret_is_authorized(*, provided: str, configured: str) -> bool:
    if not configured:
        raise MissingServiceSecretError("Required service secret is not configured")
    return bool(provided) and hmac.compare_digest(provided, configured)
