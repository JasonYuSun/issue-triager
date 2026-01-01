from app.agent import triage_issue


def test_vague_issue_forces_low_priority():
    title = "Help"
    body = "Broken"
    result = triage_issue(title, body, repo=None, url=None)
    assert result.priority == "LOW"
    assert result.missing_info_requests
