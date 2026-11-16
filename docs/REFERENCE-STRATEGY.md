# Reference Documents and Integration Strategy

This project incorporates operating principles from the user's existing reference material. The references inform architecture and workflow policy; they do not justify copying another product wholesale or claiming unverified compatibility.

## Oh My Hermes Operator Field Guide

Reference: the user's oh_my_hermes_operator_field_guide.md (11 November 2026).

Key design implications:
- Hermes remains the conversational reasoning and tool-using agent. OMH is a structured workflow/skill/contract layer, not a hidden execution runtime.
- Keep skills, playbooks, roles, harnesses and executors distinct. A role label such as Reviewer does not prove an independent reviewer ran.
- Choose the smallest workflow that protects the outcome. Do not fan out agents merely to appear sophisticated.
- Every handoff must be self-contained: goal, context, files, constraints, write boundary, acceptance criteria, verification and stop conditions.
- Separate discovery, decision, execution and proof. A plan is not implementation; an agent's done message is not test evidence.
- Parallelize only genuinely independent work. Assign one owner per mutable workspace and make integration ownership explicit.
- Keep model routing separate from executor ownership. A route recommendation does not prove a particular provider call occurred.
- Curate durable project memory. Treat it as an aid, not a source of truth; refresh consequential facts.
- Report evidence at the boundary where it was observed: command output, CI run, artifact, commit, reviewer findings or deployment health.

## OpenMausBot + Grok Bot strategy audit

Reference: the user's OpenMausBot_GrokBot_Strategy.md (research snapshot 1 November 2026).

Key design implications:
- Treat OpenMausBot as an existing provider-neutral workspace/control plane option, not something to silently install or replace. Validate actual feature/architecture fit before adding it.
- Distinguish Grok Bot, Grok Build CLI and Grok API. Their execution and billing boundaries differ.
- Do not assume ARM64 support for a desktop/computer-use agent stack. Keep Pi focused on always-on services; use the x86 ThinkPad for local CLI execution.
- Prefer connector/API integrations over brittle browser automation.
- Use narrow per-role permissions and Ask-first approvals. A shared agent account or shared browser is not an isolation boundary.
- Keep credentials out of ordinary prompts, shell history and logs. Avoid unrestricted Docker socket or root SSH access.
- Run workflows manually and validate them before scheduling them.
- Use provider diversity for independent review or genuinely different expertise, not indiscriminate duplication.

## Orchestra interpretation

Orchestra should coordinate the systems already in the user's environment, not create a second overlapping agent ecosystem:
- Pi: durable queue, approval UI, audit trail, event routing and worker registry.
- ThinkPad: execution host for installed coding agents.
- Hermes/OMH: conversation, skills, playbooks and workflow guidance.
- OpenCode/Claude Code/Codex/Gemini CLI: selectable execution adapters after host verification.
- FreeLLMAPI: model-routing/inference endpoint, not interchangeable with a coding CLI.
- Tailscale: private transport, not application authentication. Keep both network and application auth.

## Claim discipline

For every capability, record one of: implemented and tested, implemented but unverified on target hardware, configured but not tested, planned, unsupported. Never promote a planned or configured capability to working status without an observed end-to-end test.


## Upstream source links

### Hermes and Oh My Hermes
- OMH documentation: https://omher.app/docs/
- OMH skill catalog: https://omher.app/docs/skills/
- OMH model routing: https://omher.app/docs/model-routing/
- OMH source repository: https://github.com/rlaope/oh-my-hermes
- Hermes delegation: https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation
- Hermes skills: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- Hermes context files: https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files

### OpenMausBot and xAI
- OpenMausBot source repository: https://github.com/milind-soni/OpenMausBot
- OpenMausBot security documentation: https://docs.openmausbot.com/docs/security
- OpenMausBot provider documentation: https://docs.openmausbot.com/docs/providers
- xAI Grok Bot overview: https://docs.x.ai/grok-bot/overview
- xAI Grok Bot security and approvals: https://docs.x.ai/grok-bot/approvals-security-and-privacy
- xAI Grok Build: https://docs.x.ai/build/overview

Re-check these upstream documents at implementation time. Product features, CLI flags, platform support and security behavior evolve; the user's saved research snapshots are useful context, not a substitute for current official documentation.
