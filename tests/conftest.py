import os

import pytest

from app.config import get_settings

# Force tests to use the mock LLM even if OPENAI_API_KEY is set in the user's .env.
os.environ["OPENAI_API_KEY"] = ""
os.environ["APP_ENV"] = "test"


@pytest.fixture(autouse=True)
def reset_settings():
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["APP_ENV"] = "test"
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    yield
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
