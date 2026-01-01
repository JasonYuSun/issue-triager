from __future__ import annotations

import json
from typing import Any, Dict, List

from pydantic import ValidationError

from .config import get_settings
from .github_client import GitHubClient
from .llm.gemini import GeminiLLM
from .llm.mock import MockLLM
from .logging_utils import get_logger
from .prompt_builder import build_prompts
from .schemas import TriageResult
from .triage_criteria import load_triage_criteria

logger = get_logger(__name__)


def triage_issue(title: str, body: str | None, repo: str | None, url: str | None) -> TriageResult:
    settings = get_settings()
    criteria_text = load_triage_criteria()
    system_prompt, user_prompt = build_prompts(criteria_text, title, body, repo, url)

    llm_client = GeminiLLM() if settings.GEMINI_API_KEY else MockLLM()
    raw_output = llm_client.generate(system_prompt, user_prompt)

    triage = _parse_llm_output(raw_output, title, body)
    triage = _apply_vague_guard(triage, title, body)
    return triage


async def execute_actions(
    result: TriageResult,
    repo_full_name: str,
    issue_number: int,
    issue_url: str,
) -> Dict[str, Any]:
    settings = get_settings()
    comment_body = _build_comment_body(result, issue_url)
    label = f"priority:{result.priority.lower()}"

    if settings.DRY_RUN:
        logger.info("DRY_RUN enabled; skipping GitHub API calls.")
        return {
            "mode": "dry_run",
            "planned": [
                {"action": "add_label", "label": label, "issue": issue_number, "repo": repo_full_name},
                {"action": "comment", "body": comment_body},
            ],
            "notification": "on" if result.action_required else "off",
        }

    if not settings.GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is required when DRY_RUN is False")

    client = GitHubClient(token=settings.GITHUB_TOKEN, base_url=settings.GITHUB_API_BASE)

    label_resp = await client.add_label(repo_full_name, issue_number, label)
    comment_resp = await client.add_comment(repo_full_name, issue_number, comment_body)

    if result.action_required:
        logger.info("Action required for %s#%s: would notify on-call.", repo_full_name, issue_number)

    return {
        "mode": "live",
        "applied_label": label_resp,
        "comment": comment_resp,
        "notification": "sent" if result.action_required else "skipped",
    }


def _parse_llm_output(raw_output: str, title: str, body: str | None) -> TriageResult:
    cleaned = _strip_code_fences(raw_output)
    try:
        data = json.loads(cleaned)
    except Exception:
        logger.error("Failed to parse LLM output as JSON: %s", raw_output)
        return _fallback_result()

    normalized = _normalize_triage_dict(data)
    try:
        return TriageResult.model_validate(normalized)
    except ValidationError as exc:
        logger.error("LLM output failed validation: %s", exc)
        return _fallback_result()


def _strip_code_fences(text: str) -> str:
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    if "```" in text:
        text = text.replace("```", "")
    return text.strip()


def _normalize_triage_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    priority = str(data.get("priority", "LOW")).upper()
    action_required = bool(data.get("action_required", False))
    confidence_raw = data.get("confidence", 0.0)
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError):
        confidence = 0.0

    labels = data.get("labels") or []
    if not isinstance(labels, list):
        labels = []
    priority_label = f"priority:{priority.lower()}"
    other_labels = [label for label in labels if isinstance(label, str) and not label.lower().startswith("priority:")]
    labels = [priority_label] + other_labels

    reasoning = data.get("reasoning") or "LLM output missing reasoning."
    missing_info = data.get("missing_info_requests") or []
    matched_rules = data.get("matched_rules") or []

    return {
        "priority": priority,
        "action_required": action_required,
        "labels": labels,
        "reasoning": reasoning,
        "confidence": confidence,
        "missing_info_requests": missing_info,
        "matched_rules": matched_rules,
    }


def _apply_vague_guard(result: TriageResult, title: str, body: str | None) -> TriageResult:
    content = f"{title or ''} {body or ''}".strip()
    word_count = len(content.split())
    if word_count < 10 or not content:
        label = "priority:low"
        missing = result.missing_info_requests or [
            "Please provide environment, error logs, and steps to reproduce."
        ]
        matched = list(result.matched_rules)
        if "Rule D: Insufficient Information" not in matched:
            matched.append("Rule D: Insufficient Information")
        return TriageResult(
            priority="LOW",
            action_required=False,
            labels=[label],
            reasoning="Issue too vague to triage confidently; requesting more details.",
            confidence=min(result.confidence, 0.2),
            missing_info_requests=missing,
            matched_rules=matched,
        )
    return result


def _fallback_result() -> TriageResult:
    return TriageResult(
        priority="LOW",
        action_required=False,
        labels=["priority:low"],
        reasoning="LLM output invalid; requesting more information.",
        confidence=0.0,
        missing_info_requests=["Please provide environment, error logs, and steps to reproduce."],
        matched_rules=["Fallback:InvalidLLMOutput"],
    )


def _build_comment_body(result: TriageResult, issue_url: str) -> str:
    missing_info = "\n".join(f"- {item}" for item in result.missing_info_requests) if result.missing_info_requests else "None."
    matched_rules = ", ".join(result.matched_rules) if result.matched_rules else "None"
    return (
        "Automated triage result:\n"
        f"- Priority: {result.priority}\n"
        f"- Confidence: {result.confidence}\n"
        f"- Reasoning: {result.reasoning}\n"
        f"- Matched rules: {matched_rules}\n"
        f"- Missing info requests:\n{missing_info}\n"
        f"- Issue: {issue_url}"
    )
