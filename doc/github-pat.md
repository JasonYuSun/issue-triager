## How to set up a GitHub Personal Access Token (PAT) for issue-triager

The PAT is needed only when `DRY_RUN=false` so the service can add labels and comments via the GitHub API.

### Create the token
1) Go to **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**.
2) Click **Generate new token (classic)**.
3) Name: e.g., `issue-triager`.
4) Expiration: choose a sensible duration; set a reminder to rotate.
5) Scopes: check **repo** (full) or at minimum `repo:status`, `public_repo`, `repo_deployment`, `repo:invite`, `security_events`. For private repos, full `repo` is simplest.
6) Generate and copy the token once.

### Configure locally
- Add to your `.env` (or export in shell):
  - `GITHUB_TOKEN=<your token>`
  - `DRY_RUN=false` (only when you want real API calls)
- Restart the app so it picks up env changes.

### Safety tips
- Keep the token secret; do not commit `.env`.
- Use least privilege scopes when possible.
- Revoke/rotate the token if it leaks or when you leave the project.
