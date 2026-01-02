from __future__ import annotations

from openai import OpenAI

from ..config import get_settings
from ..logging_utils import get_logger
from .base import BaseLLM

logger = get_logger(__name__)


class ChatGPTLLM(BaseLLM):
    """ChatGPT client using the official openai package."""

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout_seconds: int | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.timeout = float(timeout_seconds or settings.LLM_TIMEOUT_SECONDS)
        self._client = OpenAI(api_key=self.api_key, timeout=self.timeout) if self.api_key else None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self._client:
            raise ValueError("OPENAI_API_KEY is required to use ChatGPTLLM")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:  # pragma: no cover - network path
            logger.error("ChatGPT API call failed: %s", exc)
            return ""
