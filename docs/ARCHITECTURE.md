# Architecture

## Purpose
Orchestra is a durable coordination plane for human-directed work across existing AI runtimes and multiple machines. It is not a model, agent runtime, shell, or container manager.

## Topology
The Raspberry Pi 5 hosts the Docker control plane, API, dashboard, SQLite state and event journal. The ThinkPad connects outbound over Tailscale as an execution worker and invokes tools already installed there. The browser is a client, not a state owner.

## Components
- Control plane: Fast API, task state machine, approval endpoints, worker registry, leased claims and event journal.
- Worker plane (planned): outbound worker daemon, adapter registry, project allowlist, isolated workspaces, process supervision and lease renewal.
- Agent layer: Hermes, OMH, OpenCode, Claude Code, Codex, Gemini CLI and other installed runtimes behind provider-specific adapters.
- Integrations (later): GitHub, CI, Sentry/PostHog, Vercel, MCP and browser automation.

## Lifecycle
pending_approval → queued → running → succeeded | failed. Cancellation is terminal. Expired leases are requeued while retry budget remains; otherwise they fail. Every transition should be represented in the event journal.

## Worker protocol
1. Authenticated heartbeat.
2. Atomic task claim with lease.
3. Validate task against worker policy and project-root allowlist.
4. Invoke selected adapter in an isolated workspace.
5. Renew lease while running.
6. Report bounded output and evidence.
7. Never infer permission to merge or deploy from a successful coding task.

## Persistence
SQLite WAL is suitable for one Pi instance. Do not run multiple API replicas against the same file. Move to PostgreSQL only when concurrency, multi-user requirements or query patterns justify it.

## Reliability
Separate admin and worker credentials; fail closed if secrets are missing; claim atomically; bind completion to worker identity; bound output and runtime; retain failed and expired task evidence. The current release does not yet implement worker renewal, worker daemon, migrations or multi-user auth.
