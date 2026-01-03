from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_webhook_processes_opened(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("WEBHOOK_SECRET", "")
    monkeypatch.setenv("ALLOWED_ACTIONS", "opened")
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

    response = client.post("/webhook/github", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["triage"]["priority"] in {"LOW", "MEDIUM", "HIGH"}
    assert body["triage"]["labels"]


def test_webhook_ignores_non_opened(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("WEBHOOK_SECRET", "")
    monkeypatch.setenv("ALLOWED_ACTIONS", "opened")
    get_settings.cache_clear()

    client = TestClient(app)
    payload = {
        "action": "edited",
        "repository": {"full_name": "demo/repo"},
        "issue": {
            "number": 1,
            "title": "Staging pipeline failing",
            "body": "Terraform apply failing in staging environment.",
            "html_url": "https://github.com/demo/repo/issues/1",
        },
    }

    response = client.post("/webhook/github", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body.get("ignored") is True
    assert body.get("event") == "issues"
    assert body.get("action") == "edited"
    assert "triage" not in body


def test_webhook_signature_failure(monkeypatch):
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("WEBHOOK_SECRET", "supersecret")
    monkeypatch.setenv("ALLOWED_ACTIONS", "opened")
    get_settings.cache_clear()

    client = TestClient(app)
    payload = {
        "action": "opened",
        "repository": {"full_name": "demo/repo"},
        "issue": {
            "number": 1,
            "title": "Needs signature",
            "body": "Missing signature header.",
            "html_url": "https://github.com/demo/repo/issues/2",
        },
    }

    response = client.post("/webhook/github", json=payload)
    assert response.status_code == 401
