from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException, Request

from .agent import execute_actions, triage_issue
from .config import get_settings
from .logging_utils import get_logger
from .webhook_security import is_allowed_action, verify_signature

logger = get_logger(__name__)
app = FastAPI(title="issue-triager")


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/webhook/github")
async def github_webhook(request: Request) -> dict:
    settings = get_settings()
    raw_body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256")
    if settings.WEBHOOK_SECRET:
        if not signature or not verify_signature(raw_body, settings.WEBHOOK_SECRET, signature):
            logger.warning("Signature verification failed.")
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        logger.warning("WEBHOOK_SECRET not set; skipping signature verification.")

    event = request.headers.get("X-GitHub-Event") or settings.ALLOWED_EVENT
    if event != settings.ALLOWED_EVENT:
        raise HTTPException(status_code=400, detail=f"Unsupported event: {event}")

    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    action = payload.get("action")
    if not action or not is_allowed_action(action, settings.ALLOWED_ACTIONS):
        raise HTTPException(status_code=400, detail="Unsupported action")

    repo = (payload.get("repository") or {}).get("full_name")
    issue = payload.get("issue") or {}
    issue_number = issue.get("number")
    title = issue.get("title")
    body = issue.get("body") or ""
    issue_url = issue.get("html_url") or ""

    if not repo or issue_number is None or not title:
        raise HTTPException(status_code=400, detail="Missing required issue fields")

    triage_result = triage_issue(title, body, repo, issue_url)
    actions = await execute_actions(triage_result, repo, issue_number, issue_url)

    return {
        "ok": True,
        "repo": repo,
        "issue_number": issue_number,
        "triage": triage_result.model_dump(),
        "dry_run": settings.DRY_RUN,
        "actions": actions,
    }
