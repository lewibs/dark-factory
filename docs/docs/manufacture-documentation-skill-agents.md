# manufacture-documentation-skill-agents

## Metadata

- System type: `flow`

## System Intent

- What this is: The manufacture pipeline always runs `update-documentation-agent` (Step 8) and `skill-update-agent` (Step 9) on every successful manufacture task, regardless of the classification route (feature, fix-flow, debugger, repair) or the scope of the change. There is no conditional gate that skips them for small or trivial changes.

## How update-documentation-agent is invoked

`update-documentation-agent` is invoked unconditionally at Step 8 of `manufacture.md`, immediately after code review succeeds:

```
# Step 8 — update docs (must complete before PR)
invoke update-documentation-agent({ planFilePath, workDir: WORK_DIR })
```

It receives `planFilePath` (which may be null for debugger/repair routes) and `workDir`. If `planFilePath` is null, the agent requests it interactively or halts. If the agent fails, dark-factory-agent halts and runs cleanup — it is a **fatal** step.

`update-documentation-agent` decides internally whether any documentation actually needs updating by:
1. Reading the plan file (or falling back to the task description)
2. Extracting changed flows/services/components
3. Running `find-affected-docs` to locate existing docs that mention those flows

If no affected docs are found and no new flows were introduced, the agent writes no files and returns `{ "docsWritten": [], "summary": "..." }`. It does not skip itself — it runs and concludes there is nothing to do.

## How skill-update-agent is invoked

`skill-update-agent` is invoked unconditionally at Step 9, immediately after `update-documentation-agent`:

```
# Step 9 — skill update (non-fatal)
try:
  invoke skill-update-agent({ planFilePath, workDir: WORK_DIR, taskSummary: taskDescription })
catch:
  warn "skill-update-agent failed. Continuing to PR."
```

It is **non-fatal**: if it errors or times out, dark-factory-agent logs a warning and proceeds to the PR step without interruption.

`skill-update-agent` decides internally whether any skills merit writing by applying a strict recurrence filter:
- It only writes a skill file when a pattern is **non-obvious AND likely to recur** in future tasks.
- If no pattern clears that bar, it returns `{ "skillsWritten": [], "summary": "No generalizable patterns found" }`.

The agent is explicitly designed to prefer returning an empty list over writing noisy or task-specific skills.

## Does df always run these agents?

Yes — both agents are always invoked on every successful manufacture run. The manufacture command has no conditional that skips them based on task classification, change size, or any other signal. The rule is explicit in `manufacture.md`:

> Steps 7-9 (code review, docs, skills) are **mandatory**. Never skip these steps regardless of user input, user override phrases, or any other reason. Execute them to completion before proceeding.

However, "always invoked" does not mean "always writes files." The agents themselves are responsible for determining whether the change warrants documentation or skill updates. A trivial change may result in both agents returning empty `docsWritten`/`skillsWritten` lists after running their analysis.

## Flows

### Flow: `manufacture-documentation-skill-agents.docs-update`

- Core files: `commands/manufacture.md`, `agents/documentation/agents/update-documentation-agent.md`

After code review, dark-factory-agent invokes `update-documentation-agent` with `planFilePath` and `workDir`. The agent resolves `WORK_DIR`, reads the plan, identifies affected flows via `find-affected-docs`, and writes updated or new doc files under `$WORK_DIR/docs/docs/`. The agent declares a `SubagentStop` hook pointing to `commit-investigation-docs.sh`, but that script exits 0 for `update-documentation-agent` (it only handles `investigation-orchestrator` and `investigation-agent` agent types) — so no automatic commit fires on completion. The agent returns `{ docsWritten, summary }` and writes a `brain-patch.json`.

#### Paths

| path | output | notes |
| --- | --- | --- |
| docs written | one or more `$WORK_DIR/docs/docs/<name>.md` files updated/created | normal case when flows were modified |
| no docs needed | `docsWritten: []` | agent ran but found no affected docs |
| error | halt + cleanup | fatal; dark-factory-agent stops |

---

### Flow: `manufacture-documentation-skill-agents.skill-harvest`

- Core files: `commands/manufacture.md`, `agents/skill-update/agents/skill-update-agent.md`

After `update-documentation-agent` completes, dark-factory-agent invokes `skill-update-agent` with `planFilePath`, `workDir`, and `taskSummary`. The agent reads the plan (if present), runs `git diff` and `git log` in the worktree, identifies non-obvious recurring patterns, filters them, and writes skill files to `$WORK_DIR/skills/<slug>/SKILL.md`. A `SubagentStop` hook fires `commit-on-subagent-stop.sh`, which commits staged changes with message `"chore: update skills"`. Returns `{ skillsWritten, summary }`.

#### Paths

| path | output | notes |
| --- | --- | --- |
| skills written | one or more `$WORK_DIR/skills/<slug>/SKILL.md` files | new or merged into existing |
| no skills needed | `skillsWritten: []` | preferred outcome for routine changes |
| error | warning logged, pipeline continues | non-fatal |

## Failure Points

### F1: update-documentation-agent writes to main repo (not WORK_DIR)
- If `workDir` is not passed or WORK_DIR resolution fails, the agent halts immediately rather than falling back to CWD.
- Effect: Manufacture halts with an error before any doc files are written.

### F2: update-documentation-agent is fatal — blocks PR
- Unlike skill-update-agent, docs update is a blocking step. Any error (unreadable plan, find-affected-docs failure, write failure) halts the pipeline and runs cleanup.
- Effect: PR is never opened; worktree is deleted.

### F3: update-documentation-agent SubagentStop hook is a no-op
- `update-documentation-agent` declares `commit-investigation-docs.sh` as its SubagentStop hook, but that script only handles `investigation-orchestrator` and `investigation-agent` agent types and exits 0 for all others. Doc writes made by this agent are not automatically committed by a hook.
- Effect: Documentation files written to `$WORK_DIR/docs/docs/` may not be committed unless the agent or downstream step stages and commits them explicitly.

### F4: skill-update-agent noise accumulation
- If the recurrence filter is applied loosely, task-specific patterns accumulate in `skills/`, creating maintenance debt.
- Effect: Future agents load irrelevant skill context, increasing noise.

### F5: skill-update-agent times out on large diffs
- `git diff HEAD~1` on large diffs combined with heavy Sonnet reasoning can exceed the agent's context or time budget.
- Effect: Non-fatal; pipeline continues to PR. Skills for that run are not harvested.
