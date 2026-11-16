# ThinkPad Worker — Reuse Existing Tools

The ThinkPad is the execution host. Orchestra must not reinstall or upgrade any agent CLI.

## Inventory
Run bash scripts/worker-preflight.sh from the repository on the ThinkPad. It reports installed executable paths and versions for Hermes, OMH, OpenCode, Claude Code, Codex and Gemini CLI, plus Tailscale status. It is read-only and does not install, update or authenticate anything. Do not paste credentials or full environment dumps into task prompts.

## Network
The worker makes outbound requests to the Pi. For IP-only access, set ORCHESTRA_BIND_ADDRESS on the Pi to the Pi's Tailscale IPv4 address and set ORCHESTRA_SERVER_URL to http://<pi-tailscale-ip>:8788. Tailscale encrypts traffic within the tailnet. Alternatively, keep loopback binding and use an existing Tailscale Serve HTTPS endpoint. Do not open an inbound port on the ThinkPad or overwrite existing Serve routes.

## Worker daemon
The repository includes worker.py. It polls the control plane, heartbeats, claims approved tasks, renews leases, checks cancellation, runs a configured executable with shell disabled, and reports bounded output.

Start from deploy/worker.env.example. Copy it to ~/.config/orchestra/worker.env, set restrictive permissions (chmod 600), and fill in the actual private Tailscale URL and worker token. Do not commit the populated file.

Required environment:
- ORCHESTRA_SERVER_URL: private URL reachable from the ThinkPad.
- ORCHESTRA_WORKER_TOKEN: the worker token generated on the Pi.
- ORCHESTRA_PROJECT_ROOTS: colon-separated absolute directories the worker is allowed to access.
- ORCHESTRA_EXECUTORS: JSON object mapping engine IDs to argv arrays.
- Optional ORCHESTRA_WORKER_ID, ORCHESTRA_WORKER_NAME, ORCHESTRA_WORKER_POLL_SECONDS, ORCHESTRA_WORKER_MAX_RUNTIME_SECONDS.

An argv entry may contain {project_path} or {prompt}. If {prompt} is absent, the prompt is sent on stdin. These are literal argument substitutions; no shell is involved. Configure exact CLI syntax only after inspecting the installed binary's help and testing its non-interactive mode. Do not copy a sample command blindly.

Example configuration shape (illustrative only; verify the installed CLI's actual interface):
    ORCHESTRA_EXECUTORS={"your-engine":["verified-binary","verified-flag","{prompt}"]}

The worker only inherits a small environment allowlist. If a CLI genuinely needs a particular environment variable, add only that variable name to ORCHESTRA_WORKER_ENV_ALLOWLIST. Never add all environment variables or print their values.

## Project isolation
A task must provide a project_path under one of ORCHESTRA_PROJECT_ROOTS. The worker resolves symlinks and rejects paths outside those roots. The current worker executes in the selected directory; task-level Git worktree creation is not yet implemented. Therefore, do not dispatch concurrent write tasks into the same working tree.

## Adapter verification
For each installed tool, record executable path and version, documented non-interactive mode, prompt/stdin behavior, working-directory behavior, output format, exit codes, session/resume support, sandbox and approval semantics, and cancellation behavior. Verify the actual installed version and official documentation. Never guess flags or disable provider safety controls.

## Service posture
Use a user-level systemd service, not root. Keep the token in a permission-restricted environment file. Do not grant Docker socket access or unrestricted home-directory access. Start with a harmless scratch repository and test approval, claim, lease renewal, cancellation, timeout, failure reporting and output truncation before real project work.

## Known limits
The worker has one shared worker bearer token, not per-node cryptographic identity. Project worktrees, process-level sandboxing, secret redaction and streaming logs remain planned hardening work. Do not treat a path allowlist as a complete OS sandbox.
