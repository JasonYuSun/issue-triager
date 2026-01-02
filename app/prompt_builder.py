from __future__ import annotations

from textwrap import dedent


def build_prompts(
    criteria_text: str,
    title: str,
    body: str | None,
    repo: str | None,
    url: str | None,
) -> tuple[str, str]:
    system_prompt = dedent(
        f"""
        You are the 'issue-triager' bot, a DevOps triage expert.
        Triaging Rules:
        {criteria_text}

        Return your answer strictly as JSON with no markdown or extra commentary.
        The JSON must match this schema exactly:
        {{
          "priority": "HIGH|MEDIUM|LOW",
          "action_required": true/false,
          "labels": ["priority:high|medium|low"],
          "reasoning": "short rationale",
          "confidence": 0.0-1.0,
          "matched_rules": ["rules or heuristics applied"]
        }}
        Example:
        {{
          "priority": "HIGH",
          "action_required": true,
          "labels": ["priority:high"],
          "reasoning": "Production outage impacting customers.",
          "confidence": 0.91,
          "matched_rules": ["HIGH: Production impact"]
        }}
        """
    ).strip()

    body_text = body or ""
    user_prompt = dedent(
        f"""
        Issue Title: {title}
        Issue Body: {body_text}
        Repository: {repo or 'unknown'}
        Issue URL: {url or 'unknown'}
        """
    ).strip()

    return system_prompt, user_prompt
