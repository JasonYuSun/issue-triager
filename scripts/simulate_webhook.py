from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Dict

import httpx

from app.demo_payloads import sample_issue_payload
from app.logging_utils import get_logger

logger = get_logger(__name__)


def compute_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def main() -> int:
    url = os.getenv("WEBHOOK_URL", "http://localhost:8080/webhook/github")
    secret = os.getenv("WEBHOOK_SECRET")
    payload: Dict[str, object] = sample_issue_payload()
    body = json.dumps(payload).encode()

    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Hub-Signature-256"] = compute_signature(body, secret)
    headers["X-GitHub-Event"] = "issues"

    logger.info("Sending sample webhook to %s", url)
    with httpx.Client() as client:
        response = client.post(url, headers=headers, content=body)
        print(f"Status: {response.status_code}")
        print(response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
