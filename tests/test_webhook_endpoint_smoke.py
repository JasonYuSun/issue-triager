from fastapi.testclient import TestClient

from app.main import app


def test_webhook_endpoint_smoke():
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
