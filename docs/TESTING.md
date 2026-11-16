# Testing and Verification

## Local API tests
Create a Python 3.11+ virtual environment, install requirements.txt, then run:
- python -m compileall -q orchestra worker.py tests
- PYTHONPATH=. pytest

Tests use a temporary SQLite database and fake credentials. They must never connect to the real Pi or ThinkPad.

## CI
GitHub Actions installs Python dependencies, compiles Python sources, runs API tests, and builds an ARM64 Docker image using QEMU/Buildx. A green hosted build is not proof the image was deployed or tested on the actual Raspberry Pi.

## Required test matrix before production
- Auth: missing, invalid, admin-vs-worker token separation.
- Lifecycle: create, approve, claim, complete, cancel and illegal transitions.
- Concurrency: multiple workers claiming simultaneously must never receive the same task.
- Lease: renew, expiry, bounded retry and exhausted retry budget.
- Ownership: wrong worker cannot renew, read state or complete.
- Cancellation: worker terminates process after observing cancellation.
- Worker: unavailable server, expired token, missing adapter, missing project, path traversal, symlink escape, timeout, large stdout/stderr and broken pipe.
- Adapter: missing binary, auth expired, invalid invocation, non-zero exit, malformed output and process interruption.
- Docker: non-root process, read-only root filesystem, persistent database across container replacement, ARM64 build.
- Recovery: restore a backup into an isolated test volume and verify task/event integrity.

## Evidence rules
Record exact commit SHA, CI run URL, job result, test command, target architecture and timestamp. Mark unrun checks not_observed. Do not infer Pi hardware compatibility from an x86 CI run.
