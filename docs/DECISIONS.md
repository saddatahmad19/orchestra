# Architecture Decision Records

## ADR-001 — Pi control plane, ThinkPad worker
Status: Accepted. The Pi is always-on and owns durable state. The ThinkPad hosts coding CLIs and performs execution. This separates orchestration availability from laptop uptime and avoids assuming all CLIs support ARM64.

## ADR-002 — Reuse installed tools
Status: Accepted. Orchestra does not install, update or manage Hermes, OMH, OpenCode, Claude Code, Codex, Gemini CLI or FreeLLMAPI. It discovers and invokes only tools verified on the worker.

## ADR-003 — FastAPI and SQLite
Status: Accepted for the single-node foundation. SQLite WAL is appropriate for one Pi instance. Do not run multiple API replicas against one file. Revisit PostgreSQL if concurrency or multi-user needs justify it.

## ADR-004 — Docker Compose and loopback binding
Status: Accepted. Single container, named volume, host loopback. Remote access through private Tailscale routing only.

## ADR-005 — Approval by default
Status: Accepted. Dispatch requires approval by default. Approval to dispatch does not authorize merge, deployment or external side effects.
