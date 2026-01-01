PYTHON ?= python3
VENV ?= .venv

.PHONY: install run test eval curl-demo tunnel-demo

install:
	[ -d $(VENV) ] || $(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -U pip
	$(VENV)/bin/pip install -e .

run:
	$(VENV)/bin/uvicorn app.main:app --host 0.0.0.0 --port $${PORT:-8080} --reload

test:
	$(VENV)/bin/pytest -q

eval:
	$(VENV)/bin/python scripts/eval_triage.py

curl-demo:
	$(VENV)/bin/python scripts/simulate_webhook.py

tunnel-demo:
	@echo "1) Start the server locally: make run"
	@echo "2) Start a tunnel (ngrok or cloudflared):"
	@echo "   - ngrok: ngrok http $${PORT:-8080}"
	@echo "   - cloudflared: cloudflared tunnel --url http://localhost:$${PORT:-8080}"
	@echo "3) In GitHub repo settings, add a Webhook pointing to <tunnel-url>/webhook/github"
	@echo "   - Content-Type: application/json"
	@echo "   - Secret: set to WEBHOOK_SECRET from your .env"
	@echo "   - Events: Issues"
	@echo "4) Trigger an issue event (opened/edited) to see the triager respond."
