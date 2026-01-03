# issue-triager

Agentic triage bot for GitHub Issues. **issue-triager** is an AI agent designed to automate the initial classification of DevOps support tickets. It dynamically loads `TRIAGE_CRITERIA.md`, asks an LLM to identify the priority of the issue, applies the appropriate label and comment and take actions accordingly. It acts as an interface between the customer and the support team to identify which issues require immediate attention and which can stay in the queue waiting for pickup.

## The Problem Statement: The Triage Dilemma
In a fast-paced DevOps environment, the "Support Channel" repository often suffers from two triage dilemmas:

- **Manual Triage Delay**: If the Support Team is responsible for triage, they must context-switch constantly, or high-priority issues sit in the queue for too long.
- **Inconsistent User Triage**: If customers (developers) triage their own issues, they often lack the "big picture" (e.g., understanding how a failure in a shared network component affects the whole company), leading to either "over-triaging" (marking everything as High) or "under-triaging" (missing critical outages).

## The Solution: Agentic AI
Unlike a simple keyword-based script, an Agentic AI solution can:

- **Understand Long Context**: Interpret the nuance of an issue description.
- **Make Judgments**: Compare the issue against a dynamic, version-controlled Triage Criteria document.
- **Take Action**: Not just categorize, but perform API calls to label issues, leave explanatory comments, and push notifications when on-call attention is required, potentially identifying the risky behavior from the issue description and alerting the relevant stakeholders, or calling other agents to enrich the issue, enabling customer self-service.

```mermaid
graph TD
    %% --- Definitions & Styling ---
    classDef human fill:#f9fbb2,stroke:#d4a373,stroke-width:2px,color:#000;
    classDef github fill:#24292e,stroke:#fff,stroke-width:2px,color:#fff;
    classDef agent fill:#d4edda,stroke:#28a745,stroke-width:3px,color:#000;
    classDef llm fill:#e2cdff,stroke:#6f42c1,stroke-width:2px,color:#000;
    classDef storage fill:#fff3cd,stroke:#ffc107,stroke-width:2px,stroke-dasharray: 5 5,color:#000;
    classDef future fill:#e9ecef,stroke:#6c757d,stroke-width:2px,stroke-dasharray: 5 5,color:#6c757d;

    %% --- Nodes ---
    Customer(Customer / Developer):::human
    GH_Issue[GitHub Issue Created]:::github
    
    subgraph "Agentic Triage System"
        Agent(issue-triager Agent):::agent
        CriteriaDoc(Load TRIAGE_CRITERIA.md):::storage
        LLM_Brain(LLM Brain / Judgment):::llm
    end

    Decision{Is Priority HIGH?}:::agent
    
    subgraph "Immediate Action Path (High)"
        LabelHigh[Apply Label: HIGH]:::github
        CommentHigh[Post Reasoning Comment]:::github
        PushTeam(Request Immediate Attention):::human
    end

    subgraph "Standard Routine Path (Med/Low)"
        LabelStd[Apply Label: MED or LOW]:::github
        CommentStd[Post Reasoning Comment]:::github
        IssuePool(Leave in Issue Pool / Wait for Pickup):::storage
    end

    %% --- Future Nodes ---
    FutureNotify[Future: Trigger Slack/PagerDuty Notification]:::future
    FutureTools[Future: Based on Issue Content Call Tools / Other Agents for Enrichment]:::future

    %% --- Main Flow ---
    Customer -->|Submits Support Ticket| GH_Issue
    GH_Issue -->|Webhook Trigger| Agent
    
    Agent -->|1. Read Issue Content| GH_Issue
    Agent -->|2. Fetch Rules| CriteriaDoc
    CriteriaDoc -.-> Agent
    
    Agent -->|3. Send Context + Rules| LLM_Brain
    LLM_Brain -->|4. Return Structured Judgment JSON| Agent

    %% --- Future Work Branching (Pre-action) ---
    Agent -.->|Optional| FutureTools
    FutureTools -.-> Agent

    %% --- Decision & Action Flow ---
    Agent --> Decision
    
    %% High Priority Branch
    Decision -->|Yes| LabelHigh
    LabelHigh --> CommentHigh
    CommentHigh --> PushTeam
    PushTeam -.->|Escalation| FutureNotify

    %% Standard Branch
    Decision -->|No| LabelStd
    LabelStd --> CommentStd
    CommentStd --> IssuePool
```

## Architecture
- FastAPI webhook endpoint at `/webhook/github`.
- Dynamic context injection: `TRIAGE_CRITERIA.md` is read on every request.
- LLM backends: rules-based `MockLLM` (default, deterministic) or OpenAI ChatGPT when `OPENAI_API_KEY` is set.
- Safety: webhook signature verification (HMAC SHA256) when `WEBHOOK_SECRET` is configured; fallback guard for vague issues forces LOW priority and asks for details.
- Actions: DRY_RUN=true by default; live GitHub label/comment when DRY_RUN=false and `GITHUB_TOKEN` is provided. Notifications are logged only.

## Quickstart (local)
Prereqs: Python 3.11+ available as `python3`.

1) `cp .env.example .env` and adjust values (leave `WEBHOOK_SECRET` empty for local dev).
2) `make install`
3) `make run` (serves on `http://localhost:8080`)
4) `make eval` (golden dataset, must be 100% with the mock)
5) `make curl-demo` (sends a sample webhook payload locally using TC001 from the golden dataset; override with `DEMO_CASE_ID=TC002` etc.)

LLM selection:
- The server uses ChatGPT (via the official `openai` client) when `OPENAI_API_KEY` is set in the environment (or `.env`); otherwise it falls back to the deterministic MockLLM.
- `make eval` defaults to MockLLM for deterministic results. Set `USE_CHATGPT_FOR_EVAL=1 make eval` if you want to exercise ChatGPT instead.

## Testing
- `make test` runs pytest suite (signature verification, mock LLM golden dataset, vague issue guard, webhook smoke test).
- `make eval` prints accuracy + confusion matrix for `data/golden_dataset.json`.

## Webhook usage
- Endpoint: `POST /webhook/github`
- Headers: `X-GitHub-Event: issues`, `X-Hub-Signature-256` (required only if `WEBHOOK_SECRET` is set).
- Supported actions: `opened` (default). Other issue actions (e.g., `edited`, `closed`) are ignored with a 2xx response so GitHub deliveries stay green; adjust via `ALLOWED_ACTIONS` if you want more.
- If `TRIAGE_CRITERIA.md` is missing, the API returns 500 with a clear error.

## Real GitHub demo (via tunnel)
1) Start the server locally: `make run`.
2) Start a tunnel (ngrok): see `doc/ngrok.md` for install/auth/start steps.
3) In GitHub repo settings > Webhooks: see `doc/github-webhook.md` for exact form values.
4) Trigger issue opened/edited events. Codex cannot configure GitHub for you; paste the secret and URL yourself.

## DRY_RUN vs live actions
- Default `DRY_RUN=true`: response includes intended label/comment without calling GitHub.
- To enable live actions: set `DRY_RUN=false` and `GITHUB_TOKEN=<PAT with repo scope>`. The bot adds `priority:*` label and posts a comment summarizing reasoning and matched rules using PyGithub. See `doc/github-pat.md` for PAT setup.

## ChatGPT mode
- Set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`) to use ChatGPT instead of the mock.
- The LLM must return strict JSON; invalid responses fall back to a LOW priority result asking for more info.

## Local simulation via curl helper
- `make curl-demo` sends a demo payload to `WEBHOOK_URL` (defaults to `http://localhost:8080/webhook/github`). If `WEBHOOK_SECRET` is set, the script signs the request.

## Additional docs
- `doc/ngrok.md`: installing/configuring ngrok and starting a tunnel.
- `doc/github-webhook.md`: creating and testing the GitHub webhook for issue-triager.
- `doc/github-pat.md`: creating and configuring a GitHub Personal Access Token for live actions.

## Files of interest
- `app/main.py`: FastAPI webhook handler.
- `app/agent.py`: orchestration, validation, action plan.
- `app/llm/mock.py`: deterministic rules hitting 100% on the golden dataset.
- `app/llm/chatgpt.py`: minimal ChatGPT client.
- `app/webhook_security.py`: HMAC SHA256 verification.
- `data/golden_dataset.json`: evaluation cases TC001–TC030.
- `TRIAGE_CRITERIA.md`: triage policy loaded at runtime; edits here change behavior without code changes.
