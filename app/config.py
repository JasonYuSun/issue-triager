from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )

    APP_ENV: str = "local"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    WEBHOOK_SECRET: Optional[str] = None
    ALLOWED_ACTIONS: str = "opened,edited"
    ALLOWED_EVENT: str = "issues"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    LLM_TIMEOUT_SECONDS: int = 20

    DRY_RUN: bool = True
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_BASE: str = "https://api.github.com"

    @property
    def allowed_actions(self) -> set[str]:
        return {item.strip() for item in self.ALLOWED_ACTIONS.split(",") if item.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
