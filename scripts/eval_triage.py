from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

from app.agent import triage_issue
from app.config import get_settings


def ensure_mock_llm() -> None:
    os.environ.pop("GEMINI_API_KEY", None)
    try:
        get_settings.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass


def load_dataset() -> list[dict]:
    path = Path(__file__).resolve().parent.parent / "data" / "golden_dataset.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    ensure_mock_llm()
    dataset = load_dataset()
    results = []
    confusion: dict[str, Counter] = defaultdict(Counter)

    for case in dataset:
        predicted = triage_issue(case["title"], case["description"], repo=None, url=None)
        expected = case["expected_priority"]
        confusion[expected][predicted.priority] += 1
        results.append(
            {
                "id": case["id"],
                "expected": expected,
                "predicted": predicted.priority,
                "pass": expected == predicted.priority,
                "matched_rules": predicted.matched_rules,
            }
        )

    accuracy = sum(1 for r in results if r["pass"]) / len(results)

    print(f"Accuracy: {accuracy:.2%}")
    print("\nConfusion Matrix (expected -> predicted):")
    for expected, row in confusion.items():
        print(f"{expected}: {dict(row)}")

    print("\nPer-case results:")
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"{r['id']}: expected={r['expected']}, predicted={r['predicted']} [{status}] rules={r['matched_rules']}")

    return 0 if accuracy == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
