---
name: repair
description: "Invoke the repair-agent to apply a targeted fix — skipping planning, code review, and full doc cycle — then open and merge a PR."
user-invocable: true
---

## When to use

Use `/dark-factory:repair` when you need to apply a quick, targeted change to the codebase without going through the full dark-factory planning and review cycle. Ideal for:
- Small bug fixes
- Configuration corrections
- Single-file or single-function changes
- Any repair where the fix is already clear and no design phase is needed

## How to invoke

Run the slash command:

```
/dark-factory:repair
```

You will be prompted for:
- **taskDescription** — what to fix (be specific)
- **taskName** — optional short slug for the work branch (derived automatically if omitted)

## What happens

1. An isolated work directory is created from the current branch.
2. The change is applied directly — no planning agent, no approval gate.
3. The full test suite is run; failures are fixed iteratively (up to 5 attempts).
4. If the change is significant (touches agents, skills, commands, or public APIs), related documentation is updated.
5. A PR is opened and merged automatically.
6. The work directory is removed.

## What is skipped (compared to `/dark-factory:manufacture`)

- Planning agent
- High-level code review
- Full documentation update cycle (only triggered for significant changes)
- Skill update agent
