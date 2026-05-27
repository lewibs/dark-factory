# debug-command-agent

## Metadata

- System type: `flow`

## System Intent

- What this is: The `debug-command-agent` backs the `/dark-factory:debug` slash command. It runs in-place in whatever working directory (worktree) it is invoked from — worktree setup is handled by `gotoworktree-command-agent` separately. It delegates to `debugger-agent` to identify and fix the bug (including writing a bug audit log), then runs the full post-execution pipeline (code review → docs → skills → PR). No plan file is generated; `taskDescription` is passed as fallback to downstream agents. State is passed directly between steps as local variables — no `brain.json` is created.

## Mermaid Diagram

```mermaid
flowchart TD
  User["User: /dark-factory:debug\ntaskDescription, taskName"] --> DCA

  DCA["debug-command-agent\n(runs in-place)"]

  DCA --> DA["debugger-agent\n(taskDescription)"]

  DA -->|"error"| ERR["STOP: error"]
  DA -->|"success"| CRO["code-review-orchestrator-agent"]

  CRO --> UDA["update-documentation-agent"]
  UDA --> SUA["skill-update-agent\n(non-fatal)"]
  SUA --> PRA["pr-agent"]
  PRA -->|"prUrl"| Done["Done: PR URL"]
```

## Flows

### Flow: `debugCommand`

- Test files: `N/A`
- Core files: `commands/debug.md`, `agents/dark-factory/agents/debug-command-agent.md`, `agents/debugger/agents/debugger-agent.md`

#### Types

```txt
DebugCommandInput {
  taskDescription: string (required — description of the bug)
  taskName:        string (optional — derived if absent)
}

DebugCommandOutput {
  prUrl:    string
  bugFiles: string[]  (paths to bug audit log files written)
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `debugCommand.success` | `DebugCommandInput` | `DebugCommandOutput` | happy path | bug fixed, docs updated, PR opened |
| `debugCommand.worker-error` | `DebugCommandInput` | `StandardError` | error | debugger-agent returned error |

#### Pseudocode

```
debug-command-agent(taskDescription, taskName):

  # Step 1 — derive taskName slug
  if taskName is empty:
    taskName = "debug-" + slugify(taskDescription)

  PROJECT_DIR = bash("git rev-parse --show-toplevel")

  # Step 2 — invoke debugger-agent (no brain.json created)
  result = invoke debugger-agent({ taskDescription })

  if result is error:
    report error: result.message
    STOP

  planFilePath = null  # no plan file for debugger route

  # Steps 3-6 — post-execution pipeline
  invoke code-review-orchestrator-agent({
    planFilePath: planFilePath ?? "Task: " + taskDescription,
    codePath: PROJECT_DIR
  })
  invoke update-documentation-agent({ planFilePath, workDir: PROJECT_DIR })
  try: invoke skill-update-agent({ planFilePath, workDir: PROJECT_DIR, taskSummary: taskDescription })
  prResult = invoke pr-agent({ planFilePath ?? taskDescription })

  Report: "Debug complete. PR: " + prResult.prUrl
  STOP
```

## Logs

| Source | Location |
|--------|----------|
| command agent stdout | PR URL reported directly on completion |
| bug audit logs | `docs/bugs/<date>-<slug>.md` (written by debugger-agent, persisted) |

## Deployment

- Mechanism: `local only`
- Deploy command:
  ```bash
  /dark-factory:debug
  ```
- Notes: Invoked as a Claude Code slash command. Requires the dark-factory plugin installed. The agent runs in-place in the current directory — use `/dark-factory:gotoworktree` first to land in the correct worktree. No plan file is generated — `taskDescription` is passed as fallback to code-review and pr-agent.
