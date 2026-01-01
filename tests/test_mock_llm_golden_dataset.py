import json
from pathlib import Path

from app.agent import triage_issue


def test_mock_llm_matches_golden_dataset():
    dataset_path = Path(__file__).resolve().parent.parent / "data" / "golden_dataset.json"
    cases = json.loads(dataset_path.read_text())

    for case in cases:
        result = triage_issue(case["title"], case["description"], repo=None, url=None)
        assert result.priority == case["expected_priority"]
