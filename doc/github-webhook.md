## How to set up and use a GitHub webhook for issue-triager

### Prerequisites
- Running local server: `make run` (listens on `http://localhost:8080`).
- Public URL via tunnel (ngrok or cloudflared). Example: `https://<id>.ngrok.io`.
- Shared secret value (optional but recommended) saved to your `.env` as `WEBHOOK_SECRET=...`.

### Add the webhook in GitHub
1) In your GitHub repo: **Settings → Webhooks → Add webhook**.
2) Payload URL: `<public-url>/webhook/github` (e.g., `https://<id>.ngrok.io/webhook/github`).
3) Content type: `application/json`.
4) Secret: paste the same value as `WEBHOOK_SECRET` (leave blank only for local quick tests).
5) Event: choose **Issues** (or “Let me select individual events” and tick **Issues**).
6) Save the webhook.

### Test the webhook
- Open or edit an Issue in the repo; GitHub will POST to your server.
- In your server logs you should see triage output.
- To manually replay a delivery: Webhooks page → click your webhook → Recent Deliveries → Redeliver.

### Headers to expect
- `X-GitHub-Event: issues`
- `X-Hub-Signature-256: sha256=<hmac>` (present only if `WEBHOOK_SECRET` is set; must match your server secret)

### Common gotchas
- If you see 401 “Invalid signature”, double-check the secret in GitHub matches `WEBHOOK_SECRET`.
- Keep the tunnel running; GitHub will fail if the public URL is offline.
- For dry runs, leave `DRY_RUN=true` (default). For live labeling/comments, set `DRY_RUN=false` and provide `GITHUB_TOKEN`.
