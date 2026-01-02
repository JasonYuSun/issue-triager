import json
import os

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_webhook_endpoint_smoke():
    os.environ["DRY_RUN"] = "true"
    os.environ["WEBHOOK_SECRET"] = ""
    get_settings.cache_clear()

    client = TestClient(app)
    payload = {
        "action": "opened",
        "repository": {"full_name": "demo/repo"},
        "issue": {
            "number": 1,
            "title": "Staging pipeline failing",
            "body": "Terraform apply failing in staging environment.",
            "html_url": "https://github.com/demo/repo/issues/1",
        },
    }

    body_str = json.dumps(payload)
    headers = {"Content-Type": "application/json"}

    response = client.post("/webhook/github", content=body_str, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["triage"]["priority"] in {"LOW", "MEDIUM", "HIGH"}
    assert body["triage"]["labels"]
