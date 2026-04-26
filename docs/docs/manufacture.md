# manufacture

## Metadata

- System type: `flow`

## System Intent

- What this is: The top-level user-facing orchestration flow. Given a task description, classifies the request and routes to the correct worker agent (repair, feature, debugger, or fix-flow). Repair tasks short-circuit before worktree prep and delegate entirely to `repair-agent`. All other routes create an isolated work directory, run code review, update documentation, update skills, open a PR, and clean up — all without manual intervention.

## Mermaid Diagram

```mermaid
flowchart TD
  User["User: /dark-factory:manufacture <task>"] --> DarkFactory["dark-factory-agent"]
  DarkFactory --> Classify{Classify task}
  Classify -->|repair signals| RepairAgent["repair-agent\n(manages own worktree + PR)"]
  RepairAgent --> Done2["Report: Done. PR: <url>"]
  Classify -->|new feature| Prep["prep-feature-dir.sh\n(creates isolated WORK_DIR)"]
  Classify -->|bug/crash/fix| Prep
  Classify -->|broken integration flow| Prep
  Classify -->|ambiguous| Push["PushNotification: Clarification Required"]
  Push --> User2["Ask developer one question"]
  Prep --> Feature["feature-agent"]
  Prep --> Debug["debugger-agent"]
  Prep --> FixFlow["fix-flow-orchestrator"]
  Feature --> CodeReview["code-review-orchestrator-agent"]
  Debug --> CodeReview
  FixFlow --> CodeReview
  CodeReview --> UpdateDocs["update-documentation-agent"]
  UpdateDocs --> SkillUpdate["skill-update-agent (non-fatal)"]
  SkillUpdate --> PR["pr-agent"]
  PR --> Cleanup["rm -rf WORK_DIR"]
  Cleanup --> Done["Report: Done. PR: <url>"]
```

## Flows

### Flow: `manufacture`

- Test files: `tests/`
- Core files: `agents/dark-factory/agents/dark-factory-agent.md`, `agents/dark-factory/scripts/prep-feature-dir.sh`, `commands/manufacture.md`

#### Types

```txt
ManufactureInput {
  taskDescription: string (required — verbatim user request)
  taskName: string (optional — short slug; derived from taskDescription if omitted)
}

ManufactureOutput {
  pr_url: string (URL of the merged PR)
  workDir: string (path that was cleaned up)
  skillsWritten: SkillFile[] (may be empty)
}

SkillFile {
  path: string (relative path within workDir, e.g. "skills/handle-git-conflicts/SKILL.md")
  action: "created" | "updated"
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `manufacture.repair` | `ManufactureInput` | `{ prUrl: string }` | happy path | taskDescription signals repair (small change / tweak / rename / minor update / quick fix / adjust / alter); delegates to repair-agent which manages its own worktree and PR; short-circuits before prep |
| `manufacture.feature` | `ManufactureInput` | `ManufactureOutput` | happy path | taskDescription signals new feature; routes to feature-agent |
| `manufacture.debug` | `ManufactureInput` | `ManufactureOutput` | happy path | taskDescription signals bug/crash; routes to debugger-agent |
| `manufacture.fix-flow` | `ManufactureInput` | `ManufactureOutput` | happy path | taskDescription signals broken integration; routes to fix-flow-orchestrator |
| `manufacture.ambiguous` | `ManufactureInput` | paused | clarification | agent asks developer one question before routing |
| `manufacture.worker-error` | `ManufactureInput` | `StandardError` | error | worker agent returns hard-stop; WORK_DIR cleaned up |
| `manufacture.prep-fail` | `ManufactureInput` | `StandardError` | error | prep-feature-dir.sh fails; no cleanup (work dir never created); does not apply to repair route (no prep is run) |

#### Pseudocode

```
dark-factory-agent(taskDescription, taskName):

  # Step 1 — classify and route
  classify taskDescription (first match wins):
    - repair signals ("small change", "tweak", "rename", "minor update", "quick fix", "adjust", "alter"):
        result = invoke repair-agent(taskDescription, taskName)
        if result is error: report error, STOP
        report "Done. PR: <result.prUrl>."
        STOP  # repair-agent manages its own worktree, PR, and cleanup — no further steps

    - feature keywords ("add", "build", "create", "implement", "new feature") → will route to feature-agent (Step 3)
    - flow keywords ("broken flow", "integration failing", "end-to-end", "pipeline") → will route to fix-flow-orchestrator (Step 3)
    - bug keywords ("bug", "crash", "error", "fix", "broken", "not working", "debug") → will route to debugger-agent (Step 3)
    - ambiguous → PushNotification("Clarification Required"), ask developer one question, then route

  # Step 2 — prep work dir (feature / fix-flow / debugger routes only)
  bash agents/dark-factory/scripts/prep-feature-dir.sh <taskName>
  capture WORK_DIR from stdout
  if fail: report error, STOP

  # Step 3 — delegate to worker
  cd WORK_DIR
  invoke classified worker agent with taskDescription
  if worker errors: cleanup(WORK_DIR), STOP
  planFilePath = path worker wrote its plan to (null if debugger-agent)

  # Step 4 — code review
  code-review-orchestrator-agent(planFilePath ?? "Task: <taskDescription>", WORK_DIR)
  if error: cleanup(WORK_DIR), STOP

  # Step 5 — update docs (must complete before PR)
  update-documentation-agent(planFilePath)

  # Step 5c — skill update (non-fatal)
  try: skill-update-agent(planFilePath, WORK_DIR, taskDescription)
  catch: warn and continue

  # Step 6 — open PR
  pr-agent(planFilePath ?? taskDescription)
  if error: cleanup(WORK_DIR), STOP

  # Step 7 — cleanup
  cleanup(WORK_DIR)
  report "Done. PR: <prUrl>. Skills written: <skillsWritten>."
```

## Logs

| Source | Location |
|--------|----------|
| dark-factory-agent output | Claude Code session transcript |
| prep-feature-dir.sh | stdout captured by dark-factory-agent |

## Deployment

- Mechanism: `local only` — runs inside Claude Code as a slash command
- Deploy command:
  ```bash
  # Invoked via Claude Code slash command
  /dark-factory:manufacture <task description>
  ```
- Notes: Requires Claude Code with the dark-factory plugin installed. All worker agents run in an isolated WORK_DIR cloned from the project root.
