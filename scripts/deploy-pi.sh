#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

command -v docker >/dev/null || { echo "Docker is required and was not found."; exit 1; }
docker compose version >/dev/null
command -v openssl >/dev/null || { echo "OpenSSL is required to generate secrets."; exit 1; }

if [[ ! -f .env ]]; then
  cp .env.example .env
  ADMIN_TOKEN="$(openssl rand -hex 32)"
  WORKER_TOKEN="$(openssl rand -hex 32)"
  sed -i "s|replace-with-32-plus-random-characters|$ADMIN_TOKEN|" .env
  sed -i "s|use-a-different-32-plus-random-secret|$WORKER_TOKEN|" .env
  chmod 600 .env
  echo "Created .env with fresh, distinct credentials."
else
  chmod 600 .env
  if grep -Eq 'replace-with-|use-a-different-' .env; then
    echo "Your .env still contains placeholder credentials. Edit it before deployment."
    exit 1
  fi
fi

if command -v ss >/dev/null && ss -ltn | grep -q ':8788 '; then
  echo "Port 8788 appears occupied. Inspect it before continuing."
  exit 1
fi

docker compose config --quiet
docker compose up -d --build
docker compose ps
echo
echo "Waiting for health endpoint..."
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8788/health; then
    echo
    echo "Orchestra is healthy at http://127.0.0.1:8788"
    echo "Remote access is not configured. Follow docs/OPERATIONS.md for Tailscale."
    exit 0
  fi
  sleep 2
done

echo "Orchestra did not become healthy. Inspect: docker compose logs --tail=150 orchestra"
exit 1
