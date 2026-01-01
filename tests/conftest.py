import os

import pytest

from app.config import get_settings

# Force tests to use the mock LLM even if GEMINI_API_KEY is set in the user's .env.
os.environ["GEMINI_API_KEY"] = ""


@pytest.fixture(autouse=True)
def reset_settings():
    os.environ["GEMINI_API_KEY"] = ""
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    yield
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
