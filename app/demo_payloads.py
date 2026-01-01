from __future__ import annotations

from typing import Any, Dict


def sample_issue_payload(
    title: str = "Sample issue from curl demo",
    body: str = "Testing the issue triager webhook locally.",
    repo: str = "demo/example",
    action: str = "opened",
    issue_number: int = 1,
    issue_url: str | None = None,
) -> Dict[str, Any]:
    return {
        "action": action,
        "repository": {"full_name": repo},
        "issue": {
            "number": issue_number,
            "title": title,
            "body": body,
            "html_url": issue_url or f"https://github.com/{repo}/issues/{issue_number}",
        },
    }
