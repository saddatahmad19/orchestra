#!/usr/bin/env bash
set -euo pipefail
echo "== Orchestra Pi preflight =="
uname -a
command -v docker >/dev/null && docker --version || { echo "Docker is missing"; exit 1; }
docker compose version
command -v tailscale >/dev/null && tailscale status || echo "Tailscale CLI not found"
if ss -ltn 2>/dev/null | grep -q ':8788 '; then echo "WARNING: port 8788 appears occupied"; else echo "Port 8788 appears available"; fi
echo "Read-only preflight complete. No services were changed."
