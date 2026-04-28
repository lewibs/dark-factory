# fix-broken-flow

## Metadata

- System type: `flow`

## System Intent

- What this is: The integration-flow repair flow. Given a failing integration flow name, investigates the system, generates trigger/monitor/log scripts, then loops: trigger flow → debug failure → open PR → deploy fix → repeat until the flow passes green.

## Mermaid Diagram

```mermaid
flowchart TD
  Input["fix-flow-orchestrator(flowName)"] --> Guard{flowName provided?}
  Guard -->|no| Push1["PushNotification: Input Required\nAsk for flow name"]
  Guard -->|yes| Phase1["Phase 1: investigation-agent(flowName)"]
  Phase1 --> SystemDiagram["docs/plans/system-diagram.md"]
  SystemDiagram --> Phase2["Phase 2: setup-wizard(system-diagram.md)"]
  Phase2 --> Scripts["/tmp/fix-flow-orchestrator/scripts/\ntrigger.sh\nwait-for-completion.sh\nfetch-logs.sh\n[deploy.sh]"]
  Scripts --> Phase3["Phase 3: ralph-fix-and-push(scriptPaths)"]
  Phase3 --> DebugLoop["Loop:\n1. debugger-agent(scripts + prev bugs)\n2. git commit fix locally\n3. deploy.sh (if exists)\n4. repeat until green"]
  DebugLoop -->|all green| Accumulate["Collect all docs/bugs/*.md files\nformat as PR body links"]
  Accumulate --> CreatePR["pr-agent: create 1 PR\nwith all accumulated commits"]
  CreatePR --> Done["Report: all-green. Single PR URL"]
  DebugLoop -->|stuck| Push2["PushNotification: Debugging Stuck\nAsk developer how to proceed"]
```

## Flows

### Flow: `fixBrokenFlow`

- Core files: `agents/fix-flow/agents/fix-flow-orchestrator.md`, `agents/fix-flow/agents/setup-wizard.md`, `agents/fix-flow/agents/ralph-fix-and-push.md`, `agents/fix-flow/agents/debug-flow-agent.md`

#### Types

```txt
FixBrokenFlowInput {
  flowName: string (required — name of the failing integration flow)
}

FixBrokenFlowOutput {
  all_green: true
  pr_url: string (single PR containing all accumulated fixes)
  bugFiles: string[] (all docs/bugs/*.md files created during the fix loop)
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `fixBrokenFlow.success` | `FixBrokenFlowInput` | `FixBrokenFlowOutput` | happy path | flow passes green after one or more fix iterations |
| `fixBrokenFlow.no-flow-name` | `FixBrokenFlowInput` | paused | clarification | orchestrator asks developer for flow name before proceeding |
| `fixBrokenFlow.stuck` | `FixBrokenFlowInput` | paused | clarification | debugger-agent returns same root cause twice with no progress; developer guidance required |

#### Pseudocode

```
fix-flow-orchestrator(flowName):

  # Phase 1 — understand system
  investigation-agent(flowName)
  → writes docs/plans/system-diagram.md
  assert file exists before proceeding

  # Phase 2 — generate scripts
  setup-wizard(docs/plans/system-diagram.md)
  → writes /tmp/fix-flow-orchestrator/scripts/{trigger,wait-for-completion,fetch-logs,[deploy]}.sh
  assert all required scripts exist and are executable before proceeding

  # Phase 3 — fix loop (accumulate fixes on single branch)
  ralph-fix-and-push(scriptPaths):
    bugDocPaths = []
    loop:
      debugger-agent(scriptPaths, previousBugFiles)
      → writes docs/bugs/bug-explanation-<N>.md
      bugDocPath = result.bugDocPath
      bugDocPaths.append(bugDocPath)

      if resolved (fixed == true):
        git add -A
        git commit -m "fix: resolve bug from docs/bugs/$(basename $bugDocPath)"
        break loop
      else:
        git add -A
        git commit -m "fix: attempt fix from docs/bugs/$(basename $bugDocPath)"
        previousBugFiles.append(bugDocPath)

      if deploy.sh exists: run deploy.sh

    # All bugs fixed — create single PR with all accumulated commits
    bugFileLinks = format_pr_body(bugDocPaths)
    pr-agent(
      taskDescription = "Fix integration flow: accumulated fixes from: " + bugFileLinks,
      prBody = "## Fixes\n\nThis PR accumulates all bug fixes for the integration flow:\n" + bugFileLinks
    )
    → { pr_url, merged }

    return { all_green: true, pr_url, bugFiles: bugDocPaths }

  report success with single PR URL
```

### Flow: `setupScripts`

- Core files: `agents/fix-flow/agents/setup-wizard.md`, `agents/fix-flow/skills/generate-trigger/SKILL.md`, `agents/fix-flow/skills/generate-wait-for-completion/SKILL.md`, `agents/fix-flow/skills/generate-fetch-logs/SKILL.md`, `agents/fix-flow/skills/generate-deploy/SKILL.md`

#### Types

```txt
SetupScriptsInput {
  systemDiagramPath: string (path to docs/plans/system-diagram.md)
}

SetupScriptsOutput {
  scriptPaths: ScriptPaths
}

ScriptPaths {
  trigger: string
  waitForCompletion: string
  fetchLogs: string
  deploy: string | null
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `setupScripts.success` | `SetupScriptsInput` | `SetupScriptsOutput` | happy path | all required scripts generated, verified executable |
| `setupScripts.no-deploy` | `SetupScriptsInput` | `SetupScriptsOutput { deploy: null }` | happy path | flow does not require remote deployment; deploy.sh omitted |

## Logs

| Source | Location |
|--------|----------|
| system investigation | `docs/plans/system-diagram.md` |
| bug iteration files | `docs/bugs/bug-explanation-<N>.md` |
| generated scripts | `/tmp/fix-flow-orchestrator/scripts/` |

## Deployment

- Mechanism: `local only` — invoked as a sub-agent by dark-factory-agent
- Notes: fix-flow-orchestrator is not user-invocable directly. Scripts are generated into `/tmp/` and are ephemeral. `docs/plans/system-diagram.md` and `docs/bugs/` files are kept as persistent project documentation after the flow completes.
