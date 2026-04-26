---
name: short-circuit-self-managed-route
description: "When a worker agent manages its own worktree, PR, and cleanup internally, the orchestrator must invoke it and stop before running prep-feature-dir.sh — not after."
user-invocable: false
---
## When to use

Any time a new route is added to `dark-factory-agent.md` where the target agent is responsible for its own isolation (worktree creation), PR, and cleanup — rather than relying on the orchestrator to do those steps.

## Steps

1. Identify whether the new agent creates its own worktree (calls `prep-feature-dir.sh` internally) and opens its own PR.
2. If yes, place the route check at the very top of the orchestration block — before the `prep-feature-dir.sh` call in Step 2.
3. After invoking the self-managed agent, capture `prUrl` from its return value and `STOP` immediately. Do not fall through to the worktree prep, code review, doc update, skill update, or cleanup steps.
4. The reason: if the orchestrator runs `prep-feature-dir.sh` first, a duplicate worktree will be created. When the self-managed agent also calls `prep-feature-dir.sh` with the same `taskName`, it will collide or fail.

## Notes

- The repair-agent is the canonical example: it calls `prep-feature-dir.sh` itself and returns `{ prUrl }`. The orchestrator's repair route appears before Step 2 and terminates with `STOP` after capturing `prUrl`.
- Self-managed routes also intentionally skip code review, skill-update-agent, and the full doc cycle. Document these omissions explicitly in the route comment so future readers know the skips are deliberate, not accidental.
- Agents that do NOT manage their own worktree (feature-agent, debugger-agent, fix-flow-orchestrator) should not be placed before Step 2, because they rely on the orchestrator's worktree and cleanup.
