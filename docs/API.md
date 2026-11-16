# HTTP API Reference

Base path: /api/v1. Health is /health. All API routes except health require a bearer token.

## Authentication
- Admin routes: Authorization: Bearer ORCHESTRA_ADMIN_TOKEN.
- Worker routes: Authorization: Bearer ORCHESTRA_WORKER_TOKEN.
- Tokens are distinct. Never use the admin token on the worker.
- The first UI sends the admin token from sessionStorage; keep it private-network only.

## Admin endpoints
- GET /overview — task counts, registered workers and recent events.
- POST /tasks — create task. JSON: title, prompt, engine, optional project_path, approval_required (default true), max_attempts (1–5).
- GET /tasks?status=queued&limit=50 — list tasks.
- GET /tasks/{id} — task plus lifecycle events.
- POST /tasks/{id}/approve — move pending_approval to queued.
- POST /tasks/{id}/cancel — terminal cancellation.

## Worker endpoints
- POST /workers/heartbeat — worker_id, name, hostname, platform and capabilities. Must be called before claim.
- POST /workers/claim?worker_id=... — atomically claim one queued task and receive lease_until.
- POST /workers/renew?task_id=...&worker_id=... — renew an owned running task lease.
- GET /workers/tasks/{id}/state?worker_id=... — read owned task state for cancellation polling.
- POST /tasks/{id}/complete — worker_id, status (succeeded or failed), result or error. Completion is rejected unless the worker ID matches the assigned owner.

## Example task
    curl -X POST http://127.0.0.1:8788/api/v1/tasks \
      -H "Authorization: Bearer $ORCHESTRA_ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"title":"Inspect a scratch repository","prompt":"Read only. Summarize architecture.","engine":"opencode","project_path":"/allowed/path/repo","approval_required":true}'

## State model
pending_approval → queued → running → succeeded | failed. Cancellation is terminal. A running task whose lease expires is retried while attempt < max_attempts; otherwise it becomes failed.

## Known protocol gaps
- Shared worker token is not per-node identity.
- There is no API endpoint for worker registration revocation.
- No idempotency key for task creation.
- Event retention/pagination and streaming transport are not implemented.
- A cancelled task is observed by worker polling; cancellation is not instantaneous.

## Project registry
GET /api/v1/projects lists configured projects. POST /api/v1/projects creates one. PUT /api/v1/projects/{project_id} replaces its configuration. DELETE is refused while tasks reference the project.

Project records contain name, description, repository_url, default_engine, instructions, and node_paths. node_paths maps exact worker IDs to absolute POSIX paths. Task creation can specify project_id and target_worker_id; the server resolves the correct machine-specific path and inherits the project's default engine when no override is supplied.
