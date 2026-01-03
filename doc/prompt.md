You are Codex acting as a senior Python engineer building a demo-ready local prototype repo named `issue-triager`.

Design Doc:
```markdown
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
- **Take Action**: Not just categorize, but perform API calls to label issues, leave explanatory comments, and log when on-call attention would be needed.

## 4. Technical Architecture
The architecture is designed for high readability, minimal maintenance, and local-first demos.

### Tech Stack
- **Language**: Python 3.12 (Clean, type-hinted code).
- **Web Framework**: FastAPI (For handling GitHub webhooks with high performance and readability).
- **Compute**: Container-friendly service that runs locally or can be hosted.
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
- **Notification**: If `notify_on_call` is True, the Agent logs that on-call notification would be sent (no external integrations in this version).

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
To prove the agent's value to stakeholders, we use a Golden Dataset to validate accuracy. The repo includes 30 cases in `data/golden_dataset.json`; the mock LLM is expected to classify all of them deterministically.

### Evaluation Script (eval_triage.py)
This script automates the "vibe check" into a quantitative report.

- **Input**: Loads the `golden_dataset.json`.
- **Execution**: Sends each case to the Agent logic.
- **Comparison**: Compares Agent output vs. Expected result.
- **Reporting**: Generates an Accuracy Score (%) and a Confusion Matrix.

## 8. Future Roadmap
- Multimodal Support: Use ChatGPT's multimodal capabilities to analyze screenshots of errors or architecture diagrams attached to issues.
- Issue-Resolution-Recommender: Use ChatGPT's long context window to build a system that can analyze a large number of issues and recommend most similar issues as reference to resolve the issue.

## 9. Security & Compliance
- Data Residency: Deploy within your chosen cloud region (e.g., australia-southeast1).
- Anonymization: Implementation of a pre-processing layer to scrub credentials and PII from issue descriptions before LLM ingestion.
```

Goal: Implement a local-first “agentic triage bot” that receives GitHub Issue webhooks, dynamically loads a version-controlled triage policy (TRIAGE_CRITERIA.md), asks an LLM (mock by default, ChatGPT only if OPENAI_API_KEY is set) to return a STRICT JSON contract, validates it with Pydantic, and then (dry-run by default) performs actions: label + comment via GitHub REST API using a PAT, and logs notifications.

IMPORTANT CONSTRAINTS (must comply):
- Local dev/demo first. Do NOT implement cloud-specific managed services in this version.
- Python 3.12, FastAPI, Pydantic v2, httpx, pytest.
- Default behavior uses a deterministic MOCK LLM unless OPENAI_API_KEY is set.
- The mock LLM must achieve 100% accuracy on the provided golden dataset (all cases in data/golden_dataset.json).
- GitHub actions are DRY-RUN by default, with an option to enable real calls.
- Webhook signature verification implemented (HMAC X-Hub-Signature-256) if WEBHOOK_SECRET is set; if not set, allow but warn.
- Issues only (no PRs, no comments). Handle GitHub `issues` event actions `opened` and `edited` (configurable).
- Provide BOTH local simulation (curl + sample payload + eval script) AND real GitHub webhook demo instructions via a tunnel (ngrok).
- No “TODOs” for core features. Provide clean, readable code with type hints.

================================================================================
REPOSITORY STRUCTURE (CREATE EXACTLY THIS)
================================================================================
issue-triager/
  README.md
  pyproject.toml
  .gitignore
  .env.example
  Makefile
  docker/
    Dockerfile
  app/
    __init__.py
    main.py                # FastAPI entry
    config.py              # pydantic-settings config
    schemas.py             # Pydantic models: TriageResult, GitHubPayload, etc.
    triage_criteria.py     # loads TRIAGE_CRITERIA.md from repo root
    prompt_builder.py      # builds system+user prompts and JSON instructions
    llm/
      __init__.py
      base.py              # LLM interface protocol
      mock.py              # deterministic rules-based mock -> MUST hit 100% on golden dataset
    agent.py               # orchestrates: load policy -> call llm -> validate -> action plan
    webhook_security.py    # signature verification + event filtering
    demo_payloads.py       # functions to generate sample webhook payloads for curl demo
    logging_utils.py
  data/
    golden_dataset.json
  scripts/
    eval_triage.py
    simulate_webhook.py    # optional helper: send a payload to local server
  tests/
    test_signature.py
    test_mock_llm_golden_dataset.py
    test_agent_vague_issue.py
    test_webhook_endpoint_smoke.py

================================================================================
TRIAGE POLICY FILE (REPO ROOT)
================================================================================
Create TRIAGE_CRITERIA.md at the REPO ROOT (not in data/). Use the sample policy from the design doc verbatim (Cloud Support Triage Policy v1.0). The agent must read this file at runtime for “dynamic context injection”. If missing -> 500 with clear error.

================================================================================
PYPROJECT + DEPENDENCIES
================================================================================
Use uv-style or pip editable installation is fine, but keep it simple:
- fastapi
- uvicorn[standard]
- pydantic
- pydantic-settings
- httpx
- PyGithub
- pytest
- pytest-asyncio
- rich (optional for prettier eval output; keep optional/minimal)
- python-dotenv (optional; or implement env loading in Makefile)
Add type hints. Keep linting optional.

================================================================================
CONFIG / ENV VARS (pydantic-settings)
================================================================================
Define Settings in app/config.py with defaults:
- APP_ENV: str = "local"
- PORT: int = 8080
- LOG_LEVEL: str = "INFO"

Webhook/security:
- WEBHOOK_SECRET: Optional[str] = None
- ALLOWED_ACTIONS: set[str] default {"opened","edited"} (configurable via env as comma-separated)
- ALLOWED_EVENT: str = "issues"

LLM:
- OPENAI_API_KEY: Optional[str] = None
- OPENAI_MODEL: str = "gpt-4o-mini" (configurable)
- LLM_TIMEOUT_SECONDS: int = 20
Behavior: if OPENAI_API_KEY is set -> use ChatGPT client, else use MockLLM.

GitHub actions:
- DRY_RUN: bool = True (DEFAULT)
- GITHUB_TOKEN: Optional[str] = None (required only when DRY_RUN=false)
- GITHUB_API_BASE: str = "https://api.github.com"

================================================================================
DATA: GOLDEN DATASET
================================================================================
Create data/golden_dataset.json using the provided cases TC001..TC030. Preserve fields. Do not “improve” wording.

================================================================================
SCHEMAS (STRICT JSON CONTRACT)
================================================================================
In app/schemas.py define:

1) TriagePriority = Literal["HIGH","MEDIUM","LOW"]

2) TriageResult(BaseModel):
- priority: TriagePriority
- notify_on_call: bool
- labels: list[str]
- reasoning: str
- confidence: float (0..1)
- matched_rules: list[str]

Validation rules:
- confidence must be between 0 and 1.
- labels must include exactly one label of the form `priority:high|medium|low` matching priority.
- reasoning must be non-empty.
- If issue is “too vague” (<10 words in title+body combined OR body empty and title very short), then priority MUST be LOW (enforce in agent post-validation as a safety net).

3) Define minimal GitHub webhook payload models (only fields you need) OR parse dict safely. But ensure you reliably extract:
- repository.full_name
- issue.number
- issue.title
- issue.body (may be null/empty)
- issue.html_url

================================================================================
PROMPTING (SYSTEM + USER)
================================================================================
Implement prompt builder that does:
System instruction:
- Role: “issue-triager bot / DevOps triage expert”
- Include TRIAGE_CRITERIA.md content
- Explicitly instruct: return ONLY JSON, no markdown, no extra keys
- Provide an example JSON matching schema (small)

User message:
- “Issue Title: …”
- “Issue Body: …”
- include repo + url if available

LLM output must be parsed as JSON. If the LLM returns fenced code blocks, strip fences.
If JSON invalid or schema validation fails -> return a fallback TriageResult:
- priority="LOW"
- notify_on_call=false
- labels=["priority:low"]
- reasoning="LLM output invalid; requesting more information."
- confidence=0.0
- matched_rules=["Fallback:InvalidLLMOutput"]

================================================================================
MOCK LLM (CRITICAL: MUST HIT 100% ON ALL CASES)
================================================================================
Implement app/llm/mock.py as a deterministic rules engine approximating the policy. It must return a full TriageResult and MUST classify every case in data/golden_dataset.json exactly as expected.

Required rules (cover every golden case):
- If text mentions Production OR “prod” in a context of outage, gateway errors, customer impact => HIGH
- If mentions security leak, public bucket, “Block Public Access”, vulnerability => HIGH
- If mentions any critical infra keywords listed in policy Rule C (shared-vpc-01, root-dns-zone, global-iam-policy) => HIGH AND include matched_rules with “Rule C”
- If widespread failure described (“nobody”, “entire office”, “everyone can’t connect”, “widespread”) => HIGH and include “Rule A”
- If mentions staging/uat/dev-cluster or pipeline/CI/CD/terraform apply failing for non-prod => MEDIUM
- If docs/internal wiki/onboarding links => LOW
- If sandbox password reset / sandbox cluster access / “sandbox” + minor work => LOW AND include “Rule B” when tone is loud (caps/exclamation)
- If <10 words total => LOW and request more info (Rule D)
Also:
- For TC004: despite “Urgent!!” and caps, because sandbox cluster & css demo => LOW; include matched_rules with “Rule B”
- For each result produce:
  - labels: exactly ["priority:high"] or ["priority:medium"] or ["priority:low"]
  - notify_on_call: True only for HIGH, False otherwise (for demo)
  - confidence: set high for clear matches (e.g., 0.9+), lower for vague.

Include matched_rules strings like: “HIGH: Production”, “Rule B: Loud User”, etc.

================================================================================
AGENT ORCHESTRATION
================================================================================ 
Implement app/agent.py:
- def triage_issue(title: str, body: str, repo: str|None, url: str|None) -> TriageResult
- Loads criteria text from TRIAGE_CRITERIA.md
- Builds prompt
- Calls chosen LLM client (mock or ChatGPT)
- Validates/normalizes labels
- Applies Rule D safety net if too vague (force LOW and record the matched rule)
- Returns result

Also implement an “action plan”:
- def execute_actions(result: TriageResult, repo_full_name: str, issue_number: int, issue_url: str) -> dict
- If DRY_RUN=true: do NOT call GitHub; return dict with intended API calls.
- If DRY_RUN=false: require GITHUB_TOKEN; call GitHub:
   1) apply label `priority:xxx`
   2) post comment including reasoning, confidence, matched_rules
- Notification path: just log a message when notify_on_call=true (no external integrations).

================================================================================
WEBHOOK SERVER
================================================================================
In app/main.py:
- FastAPI app with POST /webhook/github
- Read raw body bytes for signature verification.
- Validate X-GitHub-Event == "issues" (or allow missing for local simulation)
- Validate action in allowed actions.
- Extract required fields. If missing -> 400.
- Call triage_issue then execute_actions.
- Return JSON:
  {
    "ok": true,
    "repo": "...",
    "issue_number": ...,
    "triage": <TriageResult as dict>,
    "dry_run": true/false,
    "actions": {...}
  }

================================================================================
WEBHOOK SIGNATURE VERIFICATION
================================================================================
In app/webhook_security.py:
- verify_signature(raw_body: bytes, secret: str, header_signature: str) -> bool
- Header format: "sha256=<hexdigest>"
- Use hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
- Use hmac.compare_digest
If WEBHOOK_SECRET is not set: skip verification but log a warning.
Tests must cover valid and invalid signature.

Also: Add README instructions: “Codex cannot configure the GitHub UI for you; you must paste WEBHOOK_SECRET into GitHub webhook settings.”

================================================================================
EVALUATION SCRIPT
================================================================================
scripts/eval_triage.py:
- Loads data/golden_dataset.json
- For each case: call agent.triage_issue(title, description, repo=None, url=None)
- Compare result.priority vs expected_priority
- Print:
  - Accuracy %
  - Confusion matrix (rows expected, cols predicted)
  - Per-case table with id, expected, predicted, pass/fail, matched_rules
- Exit code: 0 only if accuracy == 1.0 for these 5 cases when using MockLLM
- Ensure script runs fast and deterministic.

================================================================================
TESTS
================================================================================
Implement pytest tests:
1) test_signature.py:
   - build known payload bytes
   - compute signature
   - verify true/false cases
2) test_mock_llm_golden_dataset.py:
   - load golden dataset
   - run triage_issue with mock (force mock by ensuring OPENAI_API_KEY not set)
   - assert predicted == expected for all cases
3) test_agent_vague_issue.py:
   - title/body short -> must be LOW and include the Rule D match
4) test_webhook_endpoint_smoke.py:
   - use FastAPI TestClient
   - POST sample payload
   - assert 200 and includes triage fields

================================================================================
DOCKER + MAKEFILE
================================================================================
- docker/Dockerfile: python:3.12-slim, install deps, run uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
- Makefile targets:
  - make install (create venv optional or just pip install -e .)
  - make run (uvicorn with reload)
  - make test
  - make eval
  - make curl-demo (sends a sample webhook payload to localhost; include signature if WEBHOOK_SECRET set)
  - make tunnel-demo (prints instructions for ngrok; do not actually run external tools)

================================================================================
README (DEMO-READY)
================================================================================
Write a strong README that includes:
- What this is + architecture flow
- How “dynamic TRIAGE_CRITERIA.md” changes behavior
- Local quickstart:
  1) cp .env.example .env and edit
  2) make install
  3) make run
  4) make eval
  5) make curl-demo
- Real GitHub webhook demo:
  - Using ngrok:
    - Start server
    - Start tunnel
    - Create webhook in GitHub repo settings pointing to /webhook/github
    - Set Content-Type application/json
    - Set WEBHOOK_SECRET (same as .env) and show where headers come from
    - Set events: Issues
  - Mention: “Codex cannot configure GitHub for you; you must paste the secret and URL.”
- DRY_RUN behavior:
  - default true: prints intended label/comment
  - how to enable real calls: set DRY_RUN=false and set GITHUB_TOKEN
- ChatGPT mode:
  - set OPENAI_API_KEY and optionally OPENAI_MODEL
  - model must output strict JSON; fallback occurs otherwise

================================================================================
QUALITY BAR
================================================================================
- Clean code, small functions, consistent logging.
- No hidden dependencies.
- Must run on macOS/Linux.
- The mock must be deterministic and 100% accurate on provided dataset.
- Keep everything local; do not include cloud/terraform.
- After generating files, ensure repo works logically (imports, module paths, make targets consistent).

Now implement the full repository with all files and code.
