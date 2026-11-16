# Roadmap and Definition of Done

## P0 — Foundation
- [x] Initialize public repository and root agent instructions.
- [x] Pi Docker control-plane skeleton.
- [x] Authenticated task create/list/detail, approval and cancellation.
- [x] Worker heartbeat, atomic leased claim and worker-bound completion.
- [x] SQLite persistence and event journal.
- [x] Dashboard and initial API tests.
- [ ] CI test and ARM64 image build observed green on the latest commit.

## P1 — Harden server
- [ ] Schema migrations and versioning.
- [x] Lease renewal and cancellation polling.
- [ ] Worker offline detection and status reconciliation.
- [ ] Concurrent claim/retry/expiry/race tests.
- [ ] Secure browser session (remove sessionStorage bearer token).
- [ ] Rate limits, audit identity, event retention and secret redaction.

## P2 — ThinkPad worker
- [x] Outbound worker daemon and configured worker identity.
- [x] Resolved-path project-root allowlist.
- [x] argv-only process invocation, bounded output and runtime limit.
- [x] Lease renewal and cancellation polling.
- [ ] Isolated clone/worktree manager.
- [ ] User-level service installation verified on the ThinkPad.
- [ ] End-to-end test with harmless fixture repository on the actual ThinkPad.

## P3 — Verified adapters
- [ ] Inventory actual installed binaries and versions.
- [ ] Verify invocation, auth, sandbox, approvals, stdin/output and cancellation.
- [ ] Implement and test one adapter at a time.
- [ ] Preserve native session IDs and artifacts.

## P4 — Orchestration
- [ ] Project registry, repo metadata and policies.
- [ ] Task templates, dependencies/DAG, idempotency and backoff.
- [ ] Independent reviewer and QA evidence gate.
- [ ] GitHub issue/PR and CI integrations.
- [ ] Explicit merge and deployment approvals.

## P5 — Operations maturity
- [ ] Backup automation and tested disaster recovery.
- [ ] Metrics, traces, alerts and operational dashboard.
- [ ] OIDC/multi-user support if required.
- [ ] PostgreSQL only when justified.
- [ ] Threat-model review and independent security assessment.

## Release gate
Production readiness requires P1/P2 complete, end-to-end worker execution on the actual ThinkPad, ARM64 validation on the Pi, successful backup restore rehearsal, and no unresolved critical/high security findings.
