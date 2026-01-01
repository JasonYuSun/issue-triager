from __future__ import annotations

import httpx

from ..config import get_settings
from ..logging_utils import get_logger
from .base import BaseLLM

logger = get_logger(__name__)


class GeminiLLM(BaseLLM):
    """Minimal Gemini Developer API client."""

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout_seconds: int | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.timeout = timeout_seconds or settings.LLM_TIMEOUT_SECONDS

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required to use GeminiLLM")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]},
            ]
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, params={"key": self.api_key}, json=payload)
                response.raise_for_status()
                data = response.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    logger.error("Gemini response missing candidates")
                    return ""
                first = candidates[0]
                parts = first.get("content", {}).get("parts", [])
                texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
                return "\n".join(texts).strip()
        except Exception as exc:  # pragma: no cover - network path
            logger.error("Gemini API call failed: %s", exc)
            return ""
