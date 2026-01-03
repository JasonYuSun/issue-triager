# Design Document: issue-triager (v1.0)

## 1. Project Overview
**issue-triager** is an AI agent designed to automate the initial classification of DevOps support tickets. It acts as a "first responder" to ensure critical infrastructure failures are identified in seconds, while routine requests are categorized for later review.

## 2. The Problem Statement: The Triage Dilemma
In a fast-paced DevOps environment, the "Support Channel" repository often suffers from two main issues:

- **Manual Triage Delay**: If the Support Team is responsible for triage, they must context-switch constantly, or high-priority issues sit in the queue for too long.
- **Inconsistent User Triage**: If customers (developers) triage their own issues, they often lack the "big picture" (e.g., understanding how a failure in a shared network component affects the whole company), leading to either "over-triaging" (marking everything as High) or "under-triaging" (missing critical outages).

## 3. The Solution: Agentic AI
Unlike a simple keyword-based script, an Agentic AI solution can:

- **Understand Long Context**: Interpret the nuance of an issue description.
- **Make Judgments**: Compare the issue against a dynamic, version-controlled Triage Criteria document.
- **Take Action**: Not just categorize, but perform API calls to label issues, leave explanatory comments, and log when on-call attention is required.

## 4. Technical Architecture
The architecture is designed for high readability, minimal maintenance, and cost-efficiency.

### Tech Stack
- **Language**: Python 3.12 (Clean, type-hinted code).
- **Web Framework**: FastAPI (For handling GitHub webhooks with high performance and readability).
- **Compute**: Container-friendly service that can be deployed locally or hosted.
- **AI Engine**: OpenAI ChatGPT (e.g., gpt-4o-mini) (Low latency, high reasoning capability).
- **Data Validation**: Pydantic (To ensure the LLM returns structured JSON).

## 5. Agentic Interaction Flow
This section describes how the Python Agent facilitates the conversation between the GitHub Event and the LLM (ChatGPT).

### Step 1: Trigger & Context Assembly
- **User Event**: A developer opens a GitHub Issue.
- **Webhook**: GitHub sends a POST request to the deployed `/webhook/github` endpoint.

When the webhook is received, the Agent performs "Dynamic Context Injection":

- **System Prompt**: The Agent reads the current `TRIAGE_CRITERIA.md`.
- **User Prompt**: The Agent extracts the title and body of the GitHub issue.
- **Prompt Construction**: It combines these into a single instruction, telling the LLM to behave as a "DevOps Triage Expert" following the specific rules in the criteria. For example:

```python
system_instruction = f"""
You are the 'issue-triager' bot. 
Triaging Rules:
{triage_criteria_text} 

Return your answer in JSON format matching the TriageResult schema.
"""

user_input = f"Issue Title: {issue_title}\nIssue Body: {issue_body}"
```

### Step 2: Structured Reasoning (The JSON Contract)
The Agent uses Pydantic to enforce a schema. The LLM is instructed to return a structured response, ensuring the output is machine-readable for the next steps.

### Step 3: Action Execution (The "Agentic" Step)
The Agent does not just "suggest"; it "acts" by consuming the JSON output:

- **Labeling**: Calls the GitHub API to apply the `priority:{level}` label.
- **Commenting**: Posts the reasoning as a public comment on the issue. This provides transparency to the user and the support team.
- **Notification**: If `action_required` is True, the Agent logs that on-call notification would be sent (no external integrations in this version).

## 6. The "Brain": TRIAGE_CRITERIA.md
The agent uses this document as its System Instruction. It is stored in the repository, allowing the team to update triage logic via Pull Requests without changing a single line of Python code.

### Sample Design TRIAGE_CRITERIA.md
```markdown
# Cloud Support Triage Policy (v1.0)

## Mission
To ensure that high-impact infrastructure issues are identified immediately while maintaining a clear and organized backlog for non-critical requests.

## 1. Priority Definitions

| Priority   | Criteria                                                                                 | Target Action                        |
| :--------- | :--------------------------------------------------------------------------------------- | :----------------------------------- |
| **HIGH**   | Production outages, security vulnerabilities, or failures in core shared infrastructure. | Immediate notification + Labeling.   |
| **MEDIUM** | Non-prod environment blockers, CI/CD pipeline failures, or resource requests.            | Labeling + Standard queue placement. |
| **LOW**    | General inquiries, documentation updates, or non-blocking suggestions.                   | Labeling + Backlog placement.        |

## 2. Technical Scope & Labels
- **HIGH:** Affects `Production`, `Shared-VPC`, `IAM-Root`, `DirectConnect`, or `Transit-Gateway`.
- **MEDIUM:** Affects `Staging`, `UAT`, `Dev-Cluster`, or individual developer credentials.
- **LOW:** Affects `Docs`, `Internal-Wiki`, or `Sandbox` environments.

## 3. Special & Edge Cases (Mandatory Rules)

### Rule A: The "Silent Crisis" (Contextual Escalation)
If a user describes a widespread failure (e.g., "Nobody in the London office can connect") even without using the word "Urgent," the Agent must prioritize this as **HIGH** due to the potential blast radius.

### Rule B: The "Loud User" (Tone Filtering)
Ignore excessive use of exclamation marks, caps lock, or emotional language (e.g., "FIX THIS NOW"). Prioritize based strictly on the technical impact described. If a user is shouting about a **Sandbox** password reset, it remains **LOW**.

### Rule C: Critical Infrastructure Protection
Any issue mentioning the following components must be marked **HIGH** automatically for manual verification:
- `shared-vpc-01`
- `root-dns-zone`
- `global-iam-policy`

### Rule D: Insufficient Information
If an issue contains fewer than 10 words or is too vague to categorize (e.g., "it's broken"), mark as **LOW** and use the reasoning field to request specific logs or environment details.
```

## 7. Reliability & The "Golden Dataset"
To prove the agent's value to stakeholders, we use a Golden Dataset to validate accuracy. The repo includes a 30-case dataset in `data/golden_dataset.json`.

### Evaluation Script (eval_triage.py)
This script automates the "vibe check" into a quantitative report.

- **Input**: Loads the `golden_dataset.json`.
- **Execution**: Sends each case to the Agent logic.
- **Comparison**: Compares Agent output vs. Expected result.
- **Reporting**: Generates an Accuracy Score (%) and a Confusion Matrix.
