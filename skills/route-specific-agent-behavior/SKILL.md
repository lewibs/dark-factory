---
name: route-specific-agent-behavior
description: "When a sub-agent must behave differently per work route (feature/debugger/repair/fix-flow), read brain.classification from the pre-hook-injected context — no orchestrator changes needed."
user-invocable: false
---
## When to use

When implementing or modifying a sub-agent that must produce different output depending on which dark-factory route triggered the run (feature, debugger, repair, fix-flow). Examples: pr-agent generating route-appropriate descriptions, skill-update-agent applying different extraction logic per route.

## Steps

1. In the sub-agent's pseudocode, read `brain.classification` from the injected brain context (available via the pre-hook — do NOT add a `classificationFilePath` argument or change the orchestrator).

2. Branch on the classification value:
   - `feature`: full plan doc lives at `planFilePath` (also in brain); read it verbatim.
   - `debugger`: no planFilePath is written; search `$PROJECT_DIR/docs/bugs/` for a `.md` file whose name matches `brain.taskName` (exact or prefix), falling back to the most-recently-modified file.
   - `repair` / `fix-flow`: use `planFilePath` if present; otherwise generate a summary from `git log main..HEAD --oneline` + `git diff main...HEAD --name-only`.
   - Unknown classification: fall back to `planFilePath` if provided, else the description string.

3. No changes to `dark-factory-agent.md` or brain.json are required — `classification` is already written to brain.json during the task-classifier step (Step 3 of the orchestrator) and injected by the pre-hook before every sub-agent invocation.

## Notes

- `debugger` route never sets `planFilePath` in brain.json; any code that assumes `planFilePath` is always present will silently produce an empty description for debug runs.
- The `repair` route formerly used a self-managed worktree (see `short-circuit-self-managed-route` skill); it was unified into the full orchestrator flow in April 2026, so `repair` now receives `planFilePath` when a plan was produced, but may not for small tweaks — always guard with `IF planFilePath is provided`.
- `git diff main...HEAD` (three dots) diffs the branch tip against the merge-base, which is correct for summarising branch-only changes. `git diff main..HEAD` (two dots) diffs tip-to-tip and may include unrelated main commits.
- When the classification is not in the expected set, a silent fallback keeps the agent working for future new routes without requiring a code change.
