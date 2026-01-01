from __future__ import annotations

import hashlib
import hmac
from typing import Iterable


def verify_signature(raw_body: bytes, secret: str, header_signature: str) -> bool:
    if not header_signature or "=" not in header_signature:
        return False
    try:
        algo, provided_sig = header_signature.split("=", 1)
    except ValueError:
        return False
    if algo != "sha256":
        return False
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, provided_sig)


def is_allowed_action(action: str, allowed: Iterable[str]) -> bool:
    return action in allowed
