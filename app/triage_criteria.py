from __future__ import annotations

from functools import lru_cache
from pathlib import Path


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def load_triage_criteria() -> str:
    path = get_repo_root() / "TRIAGE_CRITERIA.md"
    if not path.exists():
        raise FileNotFoundError("TRIAGE_CRITERIA.md not found at repository root")
    return path.read_text(encoding="utf-8")
