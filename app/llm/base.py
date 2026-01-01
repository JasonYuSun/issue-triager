from __future__ import annotations


class BaseLLM:
    """Interface for LLM backends."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError
