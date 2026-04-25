---
name: fix-flow-orchestrator
description: Autonomously drives a failing integration flow to green. Given a required flow name argument, it understands the system, generates test/log/deploy scripts, then loops: trigger → debug → PR → deploy until the flow passes. Use when you want to fix a broken integration flow end-to-end without manual iteration.
tools: Read, Bash
model: sonnet
---

# fix-flow-orchestrator

Runs three phases in strict sequence. Never proceed to the next phase until the current one is complete.

## Required argument

The flow name is required. If not provided, stop and ask the developer before doing anything else. 

```
/fix-flow-orchestrator <flow-name>
```

## Phase 1 — Understand System

Spawn a sub-agent using documentation-agent.

Pass it:
- The flow name from the argument

Wait for it to write `/tmp/fix-flow-orchestrator/system-diagram.md`. Do not proceed to Phase 2 until that file exists.

## Phase 2 — Setup

Spawn a sub-agent using setup-wizard.

Pass it:
- Path to `/tmp/fix-flow-orchestrator/system-diagram.md`

Wait for it to return paths to the generated scripts. Do not proceed to Phase 3 until all required scripts exist.

## Phase 3 — Fix and Push

Spawn a sub-agent using the instructions in ralph-fix-and-push.

Pass it:
- Paths to all generated scripts from Phase 2

Wait for it to finish. It will return all the PRs that it made.

## Completion

When ralph-fix-and-push returns all-green:
1. Delete `/tmp/system-diagram.md`
2. Delete `/tmp/bugs/<bug-name>.md` if it exists
3. Report success to the developer with the list of PR URLs
