# issue-triager

Agentic triage bot for GitHub Issues. It ingests GitHub issue webhooks, dynamically loads `TRIAGE_CRITERIA.md`, asks an LLM (deterministic mock by default), validates the JSON contract with Pydantic, and (dry-run by default) applies labels/comments via GitHub’s API.

## Architecture
- FastAPI webhook endpoint at `/webhook/github`.
- Dynamic context injection: `TRIAGE_CRITERIA.md` is read on every request.
- LLM backends: rules-based `MockLLM` (default, deterministic) or Gemini Developer API when `GEMINI_API_KEY` is set.
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
- The server uses Gemini (via the official `google-genai` client) when `GEMINI_API_KEY` is set in the environment (or `.env`); otherwise it falls back to the deterministic MockLLM.
- `make eval` defaults to MockLLM for deterministic results. Set `USE_GEMINI_FOR_EVAL=1 make eval` if you want to exercise Gemini instead.

## Testing
- `make test` runs pytest suite (signature verification, mock LLM golden dataset, vague issue guard, webhook smoke test).
- `make eval` prints accuracy + confusion matrix for `data/golden_dataset.json`.

## Webhook usage
- Endpoint: `POST /webhook/github`
- Headers: `X-GitHub-Event: issues`, `X-Hub-Signature-256` (required only if `WEBHOOK_SECRET` is set).
- Supported actions: `opened`, `edited` (configurable via `ALLOWED_ACTIONS`).
- If `TRIAGE_CRITERIA.md` is missing, the API returns 500 with a clear error.

## Real GitHub demo (via tunnel)
1) Start the server locally: `make run`.
2) Start a tunnel (choose one):
   - `ngrok http 8080`
   - `cloudflared tunnel --url http://localhost:8080`
3) In GitHub repo settings > Webhooks:
   - Payload URL: `<tunnel-url>/webhook/github`
   - Content type: `application/json`
   - Secret: value of `WEBHOOK_SECRET` from `.env`
   - Events: Issues
4) Trigger issue opened/edited events. Codex cannot configure GitHub for you; paste the secret and URL yourself.

## DRY_RUN vs live actions
- Default `DRY_RUN=true`: response includes intended label/comment without calling GitHub.
- To enable live actions: set `DRY_RUN=false` and `GITHUB_TOKEN=<PAT with repo scope>`. The bot adds `priority:*` label and posts a comment summarizing reasoning/matched rules/missing info.

## Gemini mode
- Set `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) to use Gemini Developer API instead of the mock.
- The LLM must return strict JSON; invalid responses fall back to a LOW priority result asking for more info.

## Local simulation via curl helper
- `make curl-demo` sends a demo payload to `WEBHOOK_URL` (defaults to `http://localhost:8080/webhook/github`). If `WEBHOOK_SECRET` is set, the script signs the request.

## Files of interest
- `app/main.py`: FastAPI webhook handler.
- `app/agent.py`: orchestration, validation, action plan.
- `app/llm/mock.py`: deterministic rules hitting 100% on the golden dataset.
- `app/llm/gemini.py`: minimal Gemini Developer API client.
- `app/webhook_security.py`: HMAC SHA256 verification.
- `data/golden_dataset.json`: evaluation cases TC001–TC005.
- `TRIAGE_CRITERIA.md`: triage policy loaded at runtime; edits here change behavior without code changes.
