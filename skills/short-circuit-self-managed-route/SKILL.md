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

- Self-managed routes also intentionally skip code review, skill-update-agent, and the full doc cycle. Document these omissions explicitly in the route comment so future readers know the skips are deliberate, not accidental.
- Agents that do NOT manage their own worktree (feature-agent, debugger-agent, repair-agent) should not be placed before Step 2, because they rely on the orchestrator's worktree and cleanup.
- **Historical note:** repair-agent was previously a self-managed route (called `prep-feature-dir.sh` internally and short-circuited the orchestrator). It was unified into the full orchestrator flow in April 2026. The repair-agent is no longer a self-managed route — it is invoked in Step 3 like any other worker and relies on the orchestrator for worktree, review, docs, skills, PR, and cleanup.

## Inverse: unifying a self-managed route back into the orchestrator

When an agent that previously used the early-exit pattern is folded back into the full orchestrator flow, reverse all of the steps above:

1. Remove the early-exit block from the orchestrator (the block that appears before Step 2 and ends with `STOP`).
2. Add the route to the Step 3 routing table (alongside other workers).
3. Update the brain.json `classification` field comment to include the new classification value.
4. Update the worker agent's description (frontmatter and prose) to clarify that it no longer manages its own worktree, PR, or cleanup — the orchestrator does.
5. Remove any `prep-feature-dir.sh` call and PR/cleanup logic from the worker agent itself.
6. Verify the worker agent's `tools:` list does not include tools it no longer needs (e.g. if it previously used `Bash` only for `prep-feature-dir.sh` and cleanup scripts, those can be removed if no other Bash usage remains).
