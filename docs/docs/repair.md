# repair

## Metadata

- System type: `flow`

## System Intent

- What this is: A lightweight repair orchestrator. Given a task description, it creates an isolated work directory, delegates implementation directly to `repair-implementation-agent` (no planning phase), optionally updates documentation for significant changes, opens and merges a PR, then cleans up. It is designed for quick targeted fixes where the change is already clear and no design phase is needed.

## Mermaid Diagram

```mermaid
flowchart TD
  User([Developer]) -->|/dark-factory:repair| CMD[commands/repair.md]
  CMD -->|taskDescription, taskName| RA[repair-agent.md]
  RA -->|taskName| PREP[prep-feature-dir.sh]
  PREP -->|WORK_DIR| RA
  RA -->|taskDescription| RIA[repair-implementation-agent.md]
  RIA -->|makes changes| CODE[Codebase Files]
  RIA -->|runs tests| TESTS[Test Suite]
  TESTS -->|pass| RIA
  TESTS -->|fail - fix and retry| RIA
  RIA -->|success, significantChange| RA
  RA -->|if significantChange| UDA[update-documentation-agent]
  UDA --> RA
  RA -->|taskDescription| PRA[pr-agent]
  PRA -->|prUrl, merged| RA
  RA -->|cleanup| CLEANUP[rm -rf WORK_DIR]
  CLEANUP --> Done([Done])
```

## Flows

### Flow: `repairOrchestration`

- Core files: `agents/dark-factory/agents/repair-agent.md`, `commands/repair.md`

#### Types

```txt
RepairInput {
  taskDescription: string (verbatim user request — what to fix or change)
  taskName: string (short slug for the work dir, e.g. "fix-login-bug"; derived if omitted)
}

RepairOrchestrationOutput {
  prUrl: string
  merged: boolean
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `repairOrchestration.success` | `RepairInput` | `RepairOrchestrationOutput{merged: true}` | `happy path` | change applied, tests pass, PR merged |
| `repairOrchestration.prep-failure` | `RepairInput` | `StandardError` | `error` | prep-feature-dir.sh fails; no cleanup needed (work dir never created) |
| `repairOrchestration.implementation-failure` | `RepairInput` | `StandardError` | `error` | repair-implementation-agent returns success=false; cleanup runs before halt |
| `repairOrchestration.pr-failure` | `RepairInput` | `StandardError` | `error` | pr-agent fails to open or merge; cleanup runs before halt |

#### Pseudocode

```
repair-agent(taskDescription, taskName):

  # Step 1 — derive taskName if not provided
  if taskName not provided:
    taskName = slugify(taskDescription, maxLen=30)

  # Step 2 — prep isolated work dir
  Run from the outer wrapper (dark_factory/):
    bash agents/dark-factory/scripts/prep-feature-dir.sh <taskName>
  Capture WORK_DIR from stdout line: WORK_DIR=<value>
  If script fails: report error and STOP (no cleanup needed)

  # Step 3 — implement directly (no planning, no routing)
  cd into WORK_DIR
  result = invoke repair-implementation-agent with: taskDescription
  If result.success == false:
    run cleanup(WORK_DIR)
    report result.error.message and STOP

  # Step 4 — optionally update docs
  If result.significantChange == true:
    invoke update-documentation-agent with: taskDescription
    (non-fatal: if it errors, warn and continue)

  # Step 5 — PR
  invoke pr-agent with: taskDescription
  If pr-agent errors or cannot merge:
    run cleanup(WORK_DIR)
    report error and STOP
  prUrl = result from pr-agent

  # Step 6 — cleanup
  cleanup(WORK_DIR)
  Report: "Done. PR: <prUrl>. Work dir <WORK_DIR> removed."
  STOP
```

---

### Flow: `repairImplementation`

- Core files: `agents/repair/agents/repair-implementation-agent.md`

#### Types

```txt
RepairImplementationInput {
  taskDescription: string
}

RepairImplementationOutput {
  success: boolean
  significantChange: boolean  -- true if change touches public API, agent instructions, skills, or user-facing commands
  error?: StandardError       -- present only when success=false
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `repairImplementation.success` | `RepairImplementationInput` | `RepairImplementationOutput{success: true}` | `happy path` | changes applied, all tests pass |
| `repairImplementation.no-tests` | `RepairImplementationInput` | `RepairImplementationOutput{success: true}` | `happy path` | no test suite found; changes applied and success returned without test verification |
| `repairImplementation.test-failure-retry` | `RepairImplementationInput` | loop | `loop` | tests fail; diagnose, fix, re-run — up to 5 iterations |
| `repairImplementation.test-failure-exhausted` | `RepairImplementationInput` | `RepairImplementationOutput{success: false}` | `error` | retry limit (5) reached with tests still failing |

#### Pseudocode

```
repair-implementation-agent(taskDescription):

  # Step 1 — understand what needs to change
  Read relevant files. Identify the minimal set of files that need modification.

  # Step 2 — apply the change
  Make the targeted change. Stay minimal — do not refactor or expand scope.
  Track which files were modified.

  # Step 3 — detect significance
  significantChange = false
  If any modified file is:
    - An agent instruction file (*.md in agents/)
    - A skill definition (SKILL.md)
    - A user-facing command (inside commands/)
    - A public API or interface boundary
  Then: significantChange = true

  # Step 4 — run tests
  Detect test runner by checking for: pytest, npm test, go test, etc.
  If no test suite found:
    return { success: true, significantChange }

  MAX_RETRIES = 5
  retries = 0
  LOOP:
    Run full test suite
    If all tests pass:
      return { success: true, significantChange }
    retries += 1
    If retries >= MAX_RETRIES:
      return { success: false, significantChange,
               error: { message: "Tests still failing after <retries> fix attempts: <last failure summary>" } }
    Read test output, identify root cause, apply targeted fix
    CONTINUE LOOP
```

## Logs

| Source | Location |
|--------|----------|
| repair-agent | stdout / Claude Code conversation |
| repair-implementation-agent | stdout / Claude Code conversation |

## Deployment

- Mechanism: `local only`
- Deploy command:
  ```bash
  # No deployment needed — agent and skill .md files are used directly by Claude Code.
  # After adding files, update the locally installed plugin:
  claude plugin marketplace add "$(pwd)"
  claude plugin update dark-factory
  claude plugin list   # confirm repair skill appears
  ```
- Notes: Changes take effect immediately when files are added. No changes to `plugin.json` are required because `"./skills/"` already covers `skills/repair/SKILL.md`.
