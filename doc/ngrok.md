## How to set up and use ngrok

ngrok gives you a public HTTPS URL that forwards traffic to a local port (useful for testing GitHub webhooks against your local server).

### Install
- macOS (Homebrew): `brew install ngrok/ngrok/ngrok`
- Linux: download from https://ngrok.com/download, unzip, move `ngrok` into your `$PATH`.

### Authenticate once
- Create an ngrok account (free tier is fine).
- Copy your authtoken from the ngrok dashboard.
- Run `ngrok config add-authtoken <token>` (stores it in `~/.config/ngrok/ngrok.yml`).

### Start a tunnel
- Start your local server, e.g. `make run` (defaults to port 8080).
- Run `ngrok http 8080`
- ngrok will print a public `https://<random>.ngrok.io` URL. Use that as the webhook base URL.

### Tips
- If you need a fixed subdomain, use an ngrok paid plan with `ngrok http --domain <name>.ngrok.io 8080`.
- Keep the ngrok terminal open while testing; closing it stops the tunnel.
