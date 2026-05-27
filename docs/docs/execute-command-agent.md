# execute-command-agent

## Metadata

- System type: `flow`

## System Intent

- What this is: The `execute-command-agent` backs the `/dark-factory:execute` slash command. It runs in-place in whatever working directory (worktree) it is invoked from — worktree setup is handled by `gotoworktree-command-agent` separately. It takes an approved plan file, runs `execution-agent` to implement all flows from the plan, then runs the full post-execution pipeline (code review → docs → skills → PR). State is passed directly between steps as local variables — no `brain.json` is created.

## Mermaid Diagram

```mermaid
flowchart TD
  User["User: /dark-factory:execute\nplanPath, taskName"] --> ECA

  ECA["execute-command-agent\n(runs in-place)"]

  ECA -->|"validate planPath"| CHECK{"Plan\nexists?"}
  CHECK -->|"no"| ERR["STOP: error"]
  CHECK -->|"yes"| EA["execution-agent\n(planPath)"]

  EA -->|"hardStop: true"| ABORT["STOP: aborted"]
  EA -->|"success"| CRO["code-review-orchestrator-agent"]

  CRO --> UDA["update-documentation-agent"]
  UDA --> SUA["skill-update-agent\n(non-fatal)"]
  SUA --> PRA["pr-agent"]
  PRA -->|"prUrl"| Done["Done: PR URL"]
```

## Flows

### Flow: `executeCommand`

- Test files: `N/A`
- Core files: `commands/execute.md`, `agents/dark-factory/agents/execute-command-agent.md`, `agents/featurework/execution/agents/execution-agent.md`

#### Types

```txt
ExecuteCommandInput {
  planPath: string (required — absolute path to approved plan file)
  taskName: string (optional — derived from plan file name if absent)
}

ExecuteCommandOutput {
  prUrl: string
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `executeCommand.success` | `ExecuteCommandInput` | `ExecuteCommandOutput` | happy path | all flows implemented, PR opened |
| `executeCommand.plan-not-found` | `ExecuteCommandInput` | `StandardError` | error | planPath does not exist |
| `executeCommand.hard-stop` | `ExecuteCommandInput` | `StandardError` | error | execution-agent hard-stop that user chose Abort for |

#### Pseudocode

```
execute-command-agent(planPath, taskName):

  # Step 1 — validate plan file exists
  if planPath not found: report error and STOP

  # Step 2 — derive taskName from plan file name if not provided
  if taskName is empty:
    taskName = basename(planPath) without .md extension and date prefix
    # e.g. "2026-05-27-add-oauth.md" → "add-oauth"

  PROJECT_DIR = bash("git rev-parse --show-toplevel")

  # Step 3 — invoke execution-agent
  invoke execution-agent({ planPath })

  if execution-agent returns hardStop: true:
    report "Execution aborted by user."
    STOP

  # Steps 4-7 — post-execution pipeline
  invoke code-review-orchestrator-agent({ planFilePath: planPath, codePath: PROJECT_DIR })
  invoke update-documentation-agent({ planFilePath: planPath, workDir: PROJECT_DIR })
  try: invoke skill-update-agent({ planFilePath: planPath, workDir: PROJECT_DIR, taskSummary: "Execute: " + planPath })
  prResult = invoke pr-agent({ planFilePath: planPath, workDir: PROJECT_DIR })

  Report: "Execution complete. PR: " + prResult.prUrl
  STOP
```

## Logs

| Source | Location |
|--------|----------|
| command agent stdout | PR URL reported directly on completion |

## Deployment

- Mechanism: `local only`
- Deploy command:
  ```bash
  /dark-factory:execute
  ```
- Notes: Invoked as a Claude Code slash command. Requires the dark-factory plugin installed. The agent runs in-place in the current directory — use `/dark-factory:goto` first to land in the correct worktree. The plan file must already exist (created by `/dark-factory:plan` or manually).
