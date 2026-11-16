# ThinkPad Worker — Reuse Existing Tools

The ThinkPad is the execution host. Orchestra must not reinstall or upgrade any agent CLI.

## Inventory
Run on the ThinkPad:
- uname -a
- python3 --version
- command -v hermes; command -v omh; command -v opencode
- command -v claude; command -v codex; command -v gemini
- tailscale status

These are read-only checks. Do not paste credentials or full environment dumps into task prompts.

## Verify each adapter
Record executable path, version, documented non-interactive mode, stdin/prompt behavior, working-directory semantics, output format, exit codes, session/resume support, sandbox and approval semantics, cancellation behavior. Check the installed binary's own help and official docs. Do not guess flags.

## Current status
The repository currently has the server-side heartbeat, claim and completion API. A production worker daemon is not yet implemented. Do not simulate a production worker by hand-calling endpoints or dispatch live coding work.

## Future service
Prefer a user-level systemd service and least-privilege account. Keep worker token in a permission-restricted environment file or systemd credential. Do not grant Docker socket access or unrestricted home-directory access.
