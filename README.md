# Orchestra

A private-first, self-hosted command center for coordinating the AI tools and machines you already operate.

## Topology
- Raspberry Pi 5: always-on Docker control plane, API, dashboard, approvals, event history and durable state.
- ThinkPad X1: remote worker that uses agent CLIs already installed on that host.
- Existing runtimes: Hermes / Oh My Hermes, OpenCode, Claude Code, Codex, Gemini CLI and other configured executors remain independent.
- Network: Tailscale private access. No public admin endpoint.

## Foundation implementation
Implemented: FastAPI service, SQLite WAL persistence, approval-gated task creation, worker heartbeat, atomic leased task claims, completion reporting bound to worker identity, event journal, dashboard, Docker packaging and API tests.

Not yet implemented: production worker daemon, verified provider adapters, lease renewal, streaming logs, project registry, worktree manager, robust migrations, multi-user auth, backup automation and full security hardening. Do not mistake the foundation for a complete autonomous coding platform.

## Raspberry Pi quick start
1. Copy .env.example to .env and run chmod 600 .env.
2. Generate two distinct values using openssl rand -hex 32.
3. Set ORCHESTRA_ADMIN_TOKEN and ORCHESTRA_WORKER_TOKEN in .env.
4. Run docker compose up -d --build.
5. Inspect docker compose ps and docker compose logs -f orchestra.
6. Check curl -fsS http://127.0.0.1:8788/health.
7. Open http://127.0.0.1:8788 on the Pi. Configure remote access only after reading docs/OPERATIONS.md.

## Development
Use Python 3.11+, create a virtual environment, install requirements.txt, set both tokens and a local ORCHESTRA_DATABASE path, then run uvicorn orchestra.main:app --reload and pytest.

## Documentation
Start with AGENTS.md. Then read docs/ARCHITECTURE.md, docs/SECURITY.md, docs/OPERATIONS.md, docs/WORKER.md, docs/ADAPTERS.md, docs/ROADMAP.md and docs/DECISIONS.md.

## ThinkPad worker

The repository includes an outbound worker daemon in worker.py. It is not enabled until you configure the private server URL, worker token, project-root allowlist and exact verified argv arrays for your installed tools. See docs/WORKER.md. The worker does not install tools, use shell execution, or bypass agent permission settings.

## Critical limitation
This is an early foundation, not a production-ready autonomous coding platform. Project worktrees, per-node credentials, secure browser sessions, secret redaction, process sandboxing, database migrations, and full observability remain open. Run only harmless scratch-project tasks until the release gates in docs/ROADMAP.md are satisfied.
