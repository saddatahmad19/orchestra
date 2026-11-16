# Agent Adapter Contract

## Principles
Existing local CLIs are executors, not dependencies to reinstall. Every adapter must be explicit, version-aware and tested. Use argv arrays, never shell interpolation. Record executable/version, exit code, duration, bounded output and native run/session ID where available.

## Candidate executors
- Hermes Agent: verify hermes --help, headless mode, session and tool policy.
- Oh My Hermes: workflow guidance and local contracts around Hermes; not a model provider or independent executor.
- OpenCode: verify installed version, run mode, auth and workspace controls.
- Claude Code: verify non-interactive mode, permissions, sandbox and stdin semantics.
- Codex CLI: verify exec mode, sandbox and approval semantics.
- Gemini CLI: verify headless mode, workspace trust and output protocol.
- FreeLLMAPI: model API/router endpoint, distinct from a local coding CLI.

## Configuration seam
ORCHESTRA_EXECUTORS is an environment JSON map from engine ID to argv array. This is not a complete adapter registry. A production adapter also needs timeout, input mode, output parser, project allowlist, environment allowlist, cancellation and approval behavior. Never enable guessed flags.
