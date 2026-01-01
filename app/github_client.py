from __future__ import annotations

import httpx

from .config import get_settings
from .logging_utils import get_logger

logger = get_logger(__name__)


class GitHubClient:
    def __init__(self, token: str, base_url: str = "https://api.github.com") -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.settings = get_settings()

    async def add_label(self, repo_full_name: str, issue_number: int, label: str) -> dict:
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{issue_number}/labels"
        payload = {"labels": [label]}
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient(timeout=self.settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Applied label %s to %s#%s", label, repo_full_name, issue_number)
            return response.json()

    async def add_comment(self, repo_full_name: str, issue_number: int, body: str) -> dict:
        url = f"{self.base_url}/repos/{repo_full_name}/issues/{issue_number}/comments"
        payload = {"body": body}
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }
        async with httpx.AsyncClient(timeout=self.settings.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Posted comment to %s#%s", repo_full_name, issue_number)
            return response.json()
