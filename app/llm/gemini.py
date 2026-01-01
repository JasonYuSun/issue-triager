from __future__ import annotations

from google import genai

from ..config import get_settings
from ..logging_utils import get_logger
from .base import BaseLLM

logger = get_logger(__name__)


class GeminiLLM(BaseLLM):
    """Gemini client using the official google-genai package."""

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout_seconds: int | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = self._normalize_model(model or settings.GEMINI_MODEL)
        self.timeout = timeout_seconds or settings.LLM_TIMEOUT_SECONDS

        self._client = genai.Client(api_key=self.api_key) if self.api_key else None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required to use GeminiLLM")

        try:
            response = self._client.models.generate_content(  # type: ignore[union-attr]
                model=self.model,
                contents=f"{system_prompt}\n\n{user_prompt}",
                config={"response_mime_type": "application/json"},
            ) if self._client else None
            if response is None:
                logger.error("Gemini client not initialized")
                return ""
            text = getattr(response, "text", "") or ""
            return text.strip()
        except Exception as exc:  # pragma: no cover - network path
            logger.error("Gemini API call failed: %s", exc)
            return ""

    @staticmethod
    def _normalize_model(name: str) -> str:
        return name if name.startswith("models/") else f"models/{name}"
