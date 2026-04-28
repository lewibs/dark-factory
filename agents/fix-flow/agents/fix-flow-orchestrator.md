---
name: fix-flow-orchestrator
user-invocable: false
description: "Autonomously drives a failing integration flow to green. Generates test/log/deploy scripts, then loops: trigger, debug, PR, deploy until the flow passes."
tools: Read, Bash, PushNotification, AskUserQuestion
model: haiku
allowed-tools: "Bash(find *), Bash(grep -r *)"
---

# fix-flow-orchestrator

Runs three phases in strict sequence. Never proceed to the next phase until the current one is complete.

## Required argument

The flow name is required. If not provided, call PushNotification with title: "Input Required" and message: "The fix-flow orchestrator needs a flow name to proceed." Then use AskUserQuestion with header "Flow Name", question "Which integration flow needs to be fixed?", and options: "Provide flow name (use Other to type it)" and "Cancel — I will reinvoke with the correct flow name". Stop and wait before doing anything else.

```
/fix-flow-orchestrator <flow-name>
```

## Phase 1 — Understand System

Spawn a sub-agent using investigation-agent.

Pass it:
- The flow name from the argument

Wait for it to return the path to the `docs/docs/` file it wrote. Then write `docs/plans/system-diagram.md` from that documentation as the working plan for this session. Do not proceed to Phase 2 until `docs/plans/system-diagram.md` exists.

## Phase 2 — Setup

Spawn a sub-agent using setup-wizard.

Pass it:
- Path to `docs/plans/system-diagram.md`

Wait for it to return paths to the generated scripts. Do not proceed to Phase 3 until all required scripts exist.

## Phase 3 — Fix and Push

Spawn a sub-agent using the instructions in ralph-fix-and-push.

Pass it:
- Paths to all generated scripts from Phase 2

Wait for it to finish. It will return a single PR with all accumulated fixes.

## Completion

When ralph-fix-and-push returns all-green:
1. Report success to the developer with the PR URL
2. Note that `docs/plans/system-diagram.md` and any `docs/bugs/` files are kept as persistent project documentation.
