from __future__ import annotations

from functools import lru_cache
from typing import Optional, Set

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)

    APP_ENV: str = "local"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    WEBHOOK_SECRET: Optional[str] = None
    ALLOWED_ACTIONS: Set[str] = Field(default_factory=lambda: {"opened", "edited"})
    ALLOWED_EVENT: str = "issues"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    LLM_TIMEOUT_SECONDS: int = 20

    DRY_RUN: bool = True
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_BASE: str = "https://api.github.com"

    @field_validator("ALLOWED_ACTIONS", mode="before")
    @classmethod
    def _parse_actions(cls, value: str | Set[str]) -> Set[str]:
        if isinstance(value, set):
            return value
        if isinstance(value, str):
            return {item.strip() for item in value.split(",") if item.strip()}
        raise TypeError("ALLOWED_ACTIONS must be a comma-separated string or a set")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
