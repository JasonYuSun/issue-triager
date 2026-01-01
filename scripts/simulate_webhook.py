from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Dict, Optional

import httpx

from app.demo_payloads import sample_issue_payload
from app.logging_utils import get_logger

logger = get_logger(__name__)


def compute_signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def load_demo_case(case_id: Optional[str]) -> Optional[dict]:
    """Load a single case from the golden dataset for richer curl-demo content."""
    dataset_path = Path(__file__).resolve().parent.parent / "data" / "golden_dataset.json"
    try:
        dataset = json.loads(dataset_path.read_text())
    except Exception as exc:  # pragma: no cover - demo helper
        logger.warning("Falling back to basic demo payload; failed to load dataset: %s", exc)
        return None

    if case_id:
        for case in dataset:
            if case.get("id") == case_id:
                return case
        logger.warning("DEMO_CASE_ID=%s not found; defaulting to first dataset case", case_id)

    return dataset[0] if dataset else None


def main() -> int:
    url = os.getenv("WEBHOOK_URL", "http://localhost:8080/webhook/github")
    secret = os.getenv("WEBHOOK_SECRET")
    demo_case = load_demo_case(os.getenv("DEMO_CASE_ID"))
    payload: Dict[str, object] = sample_issue_payload(
        title=demo_case["title"] if demo_case else "Sample issue from curl demo",
        body=demo_case["description"] if demo_case else "Testing the issue triager webhook locally.",
        repo="demo/example",
        issue_number=1,
    )
    body = json.dumps(payload).encode()

    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Hub-Signature-256"] = compute_signature(body, secret)
    headers["X-GitHub-Event"] = "issues"

    timeout = float(os.getenv("CURL_DEMO_TIMEOUT_SECONDS", "30"))
    logger.info("Sending sample webhook to %s (timeout=%ss)", url, timeout)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, headers=headers, content=body)
        print(f"Status: {response.status_code}")
        print(response.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
