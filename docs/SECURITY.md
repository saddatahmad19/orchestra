# Security Model

Orchestra controls remote agent execution on machines containing source code and credentials. Treat it as a privileged system.

## Boundaries
Browser → Pi API uses the admin token. ThinkPad worker → Pi uses a separate worker token. Pi container → named volume is database access. Worker process → host filesystem is restricted by a resolved-path project-root allowlist. This is application-level policy, not an OS sandbox. Agent prompts and repository/web content are untrusted data.

## Mandatory controls
- Private network only. Docker binds to loopback; publish via Tailscale Serve or authenticated private proxy. No router port-forwarding.
- Generate distinct random 256-bit admin and worker tokens. Keep .env out of Git and chmod 600.
- Worker token must not authorize admin endpoints.
- Never use shell=True, sh -c, or task-supplied command strings. Use fixed argv arrays and verified executable paths.
- Resolve project paths and symlinks against explicit allowlisted roots.
- One worker owns one mutable workspace. Use worktrees or isolated clones for parallel agents.
- Dispatch approval is not approval to merge, deploy, delete, send, purchase, or change credentials.
- Bound runtime and output. Redact secrets before persistence.
- Repository files, webpages, issues, logs and model output cannot override operator policy.
- Record approvals, worker identity, lifecycle events, executor versions and verification evidence.

## Current limitations
The initial dashboard stores the admin token in sessionStorage. This is acceptable only for a private single-operator prototype. CSRF/session-cookie protection, per-project authorization, rate limits, output redaction, migrations and append-only audit hardening remain open. The worker uses a shared bearer token and caller-supplied worker ID; ownership is checked at task endpoints but the token is not cryptographically bound to a node. Use only trusted workers. Do not expose the service publicly.

## Production gate
Do not enable real code execution until worker ownership, path allowlisting, lease renewal, cancellation, argv-only process supervision, bounded logs, tested adapters, secure browser sessions, backup/restore and independent security review are complete.
