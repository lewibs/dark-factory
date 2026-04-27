---
name: brain-json-lifecycle
description: "How to wire brain.json through the full dark-factory orchestration: creation, per-agent reads/writes, and deletion before worktree cleanup."
user-invocable: false
---
## When to use

When adding a new sub-agent to the dark-factory pipeline, or when modifying dark-factory-agent.md, repair-agent.md, or any worker/review/docs/skills/pr agent that participates in the brain.json lifecycle.

## Steps

1. **Orchestrator creates brain.json** — immediately after `prep-feature-dir.sh` succeeds, write a JSON file at `WORK_DIR/brain.json` with all fields initialized:
   ```
   { schemaVersion, taskName, taskDescription, workDir, phase: "init",
     planFilePath: null, bugFiles: [], prUrl: null,
     docsWritten: [], skillsWritten: [], route }
   ```
   Capture `brainPath = WORK_DIR + "/brain.json"` and pass it to every subsequent sub-agent call.

2. **Each sub-agent writes phase transitions** — on entry, read + parse `brainPath`, set `phase = "<agent>-running"`, write back. On successful exit, set the relevant output fields and `phase = "<agent>-complete"`, write back. The defined phases are:
   - `init` (set by orchestrator)
   - `worker-running` / `worker-complete` (set by feature-agent, debugger-agent, fix-flow-orchestrator)
   - `review-running` / `review-complete` (set by code-review-orchestrator-agent)
   - `docs-running` / `docs-complete` (set by update-documentation-agent)
   - `skills-running` / `skills-complete` (set by skill-update-agent)
   - `pr-running` / `pr-complete` (set by pr-agent)
   - `cleanup` (set by orchestrator just before deletion)

3. **Orchestrator reads brain after worker returns** — after the worker agent returns, re-read brain.json and prefer `brain.planFilePath` over whatever the worker returned directly, in case the worker wrote it there.

4. **Delete brain.json before calling cleanup-worktree.sh** — the cleanup script removes the entire worktree directory. Delete `brainPath` first to avoid leaving an orphaned file. This ordering is mandatory.

5. **Repair-agent creates its own brain.json copy** — repair-agent calls `prep-feature-dir.sh` in its own WORK_DIR, so it creates a new brain.json at `repairBrainPath = WORK_DIR + "/brain.json"` with `route: "repair"` and `phase: "worker-running"`. It writes `prUrl` and `phase: "pr-complete"` before its own cleanup. The outer orchestrator's `brainPath` (if provided) is ignored for repair's internal state.

## Notes

- brain.json is ephemeral — it is created per-run and deleted before worktree cleanup. It must never persist between runs.
- The repair route is special: it is a self-managed route (see `short-circuit-self-managed-route` skill) that creates its own brain.json rather than receiving one from the orchestrator.
- brain.json lives at `<WORK_DIR>/brain.json`. Never pass a path derived from any other location.
- If a sub-agent fails to write brain.json (e.g., permissions error), treat it as non-fatal — log a warning and continue. The orchestrator should not halt the run over a brain.json write failure from a sub-agent.
