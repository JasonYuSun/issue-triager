import os

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def reset_settings():
    os.environ.pop("GEMINI_API_KEY", None)
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    yield
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
