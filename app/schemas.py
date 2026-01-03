from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

TriagePriority = Literal["HIGH", "MEDIUM", "LOW"]


class TriageResult(BaseModel):
    priority: TriagePriority
    notify_on_call: bool
    labels: List[str] = Field(default_factory=list)
    reasoning: str
    confidence: float
    matched_rules: List[str] = Field(default_factory=list)

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return value

    @field_validator("reasoning")
    @classmethod
    def reasoning_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("reasoning must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_labels(self) -> "TriageResult":
        expected_label = f"priority:{self.priority.lower()}"
        priority_labels = [label.lower() for label in self.labels if label.lower().startswith("priority:")]
        if expected_label not in priority_labels:
            raise ValueError("labels must include the matching priority label")
        if priority_labels.count(expected_label) != 1:
            raise ValueError("labels must include exactly one matching priority label")
        return self


class Repository(BaseModel):
    full_name: str


class Issue(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    html_url: Optional[str] = None


class GitHubPayload(BaseModel):
    action: str
    repository: Repository
    issue: Issue
