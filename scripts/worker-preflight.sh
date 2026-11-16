#!/usr/bin/env bash
set -u

echo "== Orchestra worker preflight (run on any execution node) =="
uname -a
python3 --version 2>&1 || true
echo

for binary in hermes omh opencode claude codex gemini; do
  if command -v "$binary" >/dev/null 2>&1; then
    path="$(command -v "$binary")"
    echo "-- $binary: $path"
    timeout 8 "$binary" --version 2>&1 | head -n 4 || true
  else
    echo "-- $binary: not found (no installation attempted)"
  fi
done

echo
if command -v tailscale >/dev/null 2>&1; then
  tailscale status 2>&1 | head -n 20
else
  echo "Tailscale CLI not found."
fi

echo
echo "Preflight is read-only. It does not install, update, authenticate, or configure any tool."
echo "Review the installed CLI help and official docs before setting ORCHESTRA_EXECUTORS."
