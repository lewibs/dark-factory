# Agents

## Metadata

- System type: `library`
- Owner: dark-factory plugin
- Source directory: `agents/`
- Agent count: 24 agent markdown files across 9 subsystems

## System Intent

- What this is: The `agents/` directory contains all orchestration logic for Dark Factory. Agents are markdown files with YAML front-matter that Claude Code loads as sub-agents. Each agent has a narrowly-scoped responsibility and delegates all writing/editing to other agents or skills. No agent writes code directly — they orchestrate.
- Primary consumer(s): Claude Code runtime (loads agents via front-matter), `/dark-factory:manufacture` command (entry point).
- Boundary: Only agent `.md` files. No Python, no shell scripts (except via `allowed-tools`).

## Mermaid Diagram

```mermaid
flowchart TD
  User([Developer]) -->|/dark-factory:manufacture| DFA[dark-factory-agent\nmodel: haiku]

  DFA -->|repair signals| RepA[repair-agent]
  DFA -->|new feature| FA[feature-agent]
  DFA -->|broken flow| FFO[fix-flow-orchestrator]
  DFA -->|bug / crash| DA[debugger-agent]
  DFA -->|ambiguous| PN[PushNotification → clarify]
  RepA -->|taskDescription| RepIA[repair-agent\n agents/repair/agents/]
  RepIA -->|success or failure| RepA
  RepA -->|returns to orchestrator| DFA

  FA --> PA[planning-agent\n(Haiku orchestrator)]
  PA -->|phase=draft_plan / mermaid / flows| SPA[sub-planning-agent\n(Sonnet worker)]
  SPA -->|researches codebase| IVA2[investigation-agent]
  SPA -->|writes plan file| PF[docs/plans/YYYY-MM-DD-slug.md]
  SPA -->|url + summary| PA
  PA -->|planPath + summary| FA
  FA -->|"{ status: question, question, options, planPath }"| DFA
  DFA -->|AskUserQuestion: approve each phase| Dev2([Developer])
  Dev2 -->|answer| DFA
  DFA -->|"re-invoke feature-agent\n(answer, planPath)"| FA
  FA -->|"{ status: done, planPath }"| DFA
  DFA -->|planPath| EA[execution-agent]
  EA --> SkelA[skeleton-agent]
  EA --> TA[testing-agent]
  EA --> IA[implementation-agent]

  FFO --> IVA[investigation-agent]
  FFO --> SW[setup-wizard]
  FFO --> RFP[ralph-fix-and-push]
  RFP --> DFA2[debug-flow-agent]
  DFA2 --> DA

  DFA -->|after any worker| CRO[code-review-orchestrator-agent]
  CRO --> HLR[high-level-review-agent]
  CRO --> LLR[low-level-review-agent]
  CRO --> RA[resolver-agent]

  DFA -->|after code review| UDA[update-documentation-agent]
  DFA -->|after docs| SUA[skill-update-agent]
  DFA -->|after skills| PRA[pr-agent]
  PRA --> RPI[resolve-pr-issue]
```

## Flows

### Flow: `manufacture`

- Core files: `agents/dark-factory/agents/dark-factory-agent.md`

#### Types

```txt
TaskInput {
  taskDescription: string (verbatim user request)
  taskName: string (optional short slug; derived from taskDescription if omitted)
}

BrainState {
  taskDescription:  string
  taskName:         string
  workDir:          string   (absolute path to worktree)
  classification:   string   (one of: feature | fix-flow | debugger | repair)
  planFilePath:     string | null  (written by worker via brain-patch.json; null until planning completes)
  bugFiles:         string[] | null
  prUrl:            string | null  (written by pr-agent via brain-patch.json)
  docsWritten:      string[] | null
  skillsWritten:    string[] | null
  phases: {
    prep-running, prep-complete,
    worker-running, worker-complete,
    review-running, review-complete,
    docs-running, docs-complete,
    skills-running, skills-complete,
    pr-running, pr-complete,
    cleanup-running, cleanup-complete
  }  (boolean flags; *-running set by pre-tool-use-hook, *-complete set by post-tool-use-hook)
}

BrainPatch {
  // Subset of BrainState output fields written by sub-agents to $WORK_DIR/brain-patch.json.
  // Sub-agents never set phase flags — hooks own those.
  planFilePath?:  string
  bugFiles?:      string[]
  prUrl?:         string
  docsWritten?:   string[]
  skillsWritten?: string[]
}

ManufactureOutput {
  prUrl: string
  skillsWritten: string[]
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `manufacture.repair` | `TaskInput` | `ManufactureOutput` | `happy path` | Routes to repair-agent; runs code-review, docs, skills, PR, cleanup — same as all other routes |
| `manufacture.feature` | `TaskInput` | `ManufactureOutput` | `happy path` | Routes to feature-agent; runs code-review, docs, skills, PR, cleanup |
| `manufacture.fixFlow` | `TaskInput` | `ManufactureOutput` | `happy path` | Routes to fix-flow-orchestrator |
| `manufacture.debug` | `TaskInput` | `ManufactureOutput` | `happy path` | Routes to debugger-agent; planFilePath is null |
| `manufacture.ambiguous` | `TaskInput` | PushNotification + clarifying question | `branch` | Sends PushNotification before asking developer |
| `manufacture.workerError` | `TaskInput` | `StandardError` | `error` | Worker returns error or hard-stop; cleanup runs before halt |
| `manufacture.prepFailure` | `TaskInput` | `StandardError` | `error` | prep-feature-dir.sh fails; no cleanup needed |

---

### Flow: `featurework`

- Core files: `agents/featurework/agents/feature-agent.md`, `agents/featurework/planning/agents/planning-agent.md`, `agents/featurework/planning/agents/sub-planning-agent.md`, `agents/featurework/planning/templates/plan-template.md`, `agents/featurework/execution/agents/execution-agent.md`, `agents/featurework/execution/agents/skeleton-agent.md`, `agents/featurework/execution/agents/testing-agent.md`, `agents/featurework/execution/agents/implementation-agent.md`, `agents/featurework/execution/skills/deviation-protocol/SKILL.md`, `skills/create-mermaid-diagram/SKILL.md`

#### Types

```txt
FeatureAgentInput {
  taskDescription: string       (first invocation)
  answer: string | null         (re-invocation: user's answer to the returned question)
  planPath: string | null       (re-invocation: path to existing plan file)
}

FeatureAgentResult =
  | { status: "question", question: string, options: string[], planPath: string, phase: string }
  | { status: "done", planPath: string }
  | { status: "hard-stop", reason: string }

PlanFile {
  path: string (docs/plans/<date>-<slug>.md)
  approved: boolean
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `featurework.approved` | `FeatureAgentInput{taskDescription}` | `FeatureAgentResult{status:"done", planPath}` | `happy path` | feature-agent returns structured question objects (`{ status: "question" }`) to dark-factory-agent for each planning phase (draft, mermaid, flows); dark-factory-agent calls AskUserQuestion at depth-2 and re-invokes feature-agent with the answer; after all phases approved, execution-agent implements |
| `featurework.feedbackLoop` | `FeatureAgentInput{answer, planPath}` | `FeatureAgentResult{status:"question"}` | `loop` | Developer provides feedback during any phase; dark-factory-agent passes answer to feature-agent on re-invocation; feature-agent re-spawns planning-agent for that phase and returns a new question; loop repeats per-phase until explicit approval |
| `featurework.hardStop` | `FeatureAgentInput` | `FeatureAgentResult{status:"hard-stop"}` | `error` | implementation-agent triggers deviation-protocol; feature-agent returns hard-stop to dark-factory-agent; if architecture changed, deviation-protocol invokes `skills/create-mermaid-diagram/SKILL.md` to update the diagram before halting; dark-factory-agent runs cleanup |

---

### Flow: `fixFlow`

- Core files: `agents/fix-flow/agents/fix-flow-orchestrator.md`, `agents/fix-flow/agents/setup-wizard.md`, `agents/fix-flow/agents/ralph-fix-and-push.md`, `agents/fix-flow/agents/debug-flow-agent.md`

#### Types

```txt
FixFlowInput {
  flowName: string (name of the failing integration flow)
}

DebugFlowInput {
  triggerScriptPath: string
  waitScriptPath: string
  fetchLogsScriptPath: string
}

DebugFlowOutput {
  bugFilePath: string (docs/bugs/bug-explanation-<N>.md)
  exitCode: number (0 = flow passed, 1 = flow failed)
}

FixFlowOutput {
  prUrls: string[]
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `fixFlow.success` | `FixFlowInput` | `FixFlowOutput` | `happy path` | investigation → setup → ralph-fix-and-push loop until flow green; debug-flow-agent triggers + fetches logs per iteration |
| `fixFlow.flowPassed` | `DebugFlowInput` | `DebugFlowOutput{exitCode=0}` | `happy path` | debug-flow-agent runs trigger.sh + wait-for-completion.sh; flow succeeds; no logging or debug needed |
| `fixFlow.flowFailed` | `DebugFlowInput` | `DebugFlowOutput{exitCode=1}` | `branch` | flow fails; debug-flow-agent fetches logs and delegates to debugger-agent for fix |
| `fixFlow.missingFlowName` | `FixFlowInput{flowName=null}` | PushNotification + halt | `error` | fix-flow-orchestrator sends PushNotification before asking developer for flow name |

---

### Flow: `codeReview`

- Core files: `agents/code-review/agents/code-review-orchestrator-agent.md`, `agents/code-review/agents/high-level-review-agent.md`, `agents/code-review/agents/low-level-review-agent.md`, `agents/code-review/agents/resolver-agent.md`

#### Types

```txt
ReviewInput {
  planFilePath: string | "Task: <description>"
  codePath: string
}

ReviewOutput {
  status: "complete"
  anyRemaining: boolean (false when all issues are resolved; true if max iterations hit)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `codeReview.clean` | `ReviewInput` | `ReviewOutput{anyRemaining=false}` | `happy path` | No issues found; resolver loop exits immediately |
| `codeReview.issuesFound` | `ReviewInput` | `ReviewOutput{anyRemaining=false}` | `happy path` | Resolver loop runs up to 10 iterations until all issues checked off |
| `codeReview.maxIterations` | `ReviewInput` | `StandardError` | `error` | Resolver loop exceeds 10 iterations without clearing all items; orchestrator halts with stuck-items description |

---

### Flow: `documentation`

- Core files: `agents/documentation/agents/investigation-agent.md`, `agents/documentation/agents/update-documentation-agent.md`, `agents/documentation/agents/detect-drift-agent.md`

#### Types

```txt
DocUpdateInput {
  planFilePath: string | null
}

DocUpdateOutput {
  filesUpdated: string[]
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `documentation.update` | `DocUpdateInput` | `DocUpdateOutput` | `happy path` | update-documentation-agent identifies affected flows and updates docs/docs/ files |
| `documentation.missingPlan` | `DocUpdateInput{planFilePath=null}` | PushNotification + error | `error` | update-documentation-agent sends PushNotification before halting |
| `documentation.driftDetected` | DetectDriftInput | drift report | `branch` | detect-drift-agent flags stale docs; fixes straightforward drift in place (investigation-agent does not perform staleness checks — it returns existing docs as authoritative) |

---

### Flow: `pr`

- Core files: `agents/pr/agents/pr-agent.md`, `agents/pr/agents/resolve-pr-issue.md`

#### Types

```txt
PRInput {
  planFilePath: string | taskDescription
}

PROutput {
  pr_url: string
  status: "ready"
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `pr.ready` | `PRInput` | `PROutput{status="ready"}` | `happy path` | PR opens, CI passes, comment threads resolved, returns ready for caller to merge |
| `pr.ciFailure` | `PRInput` | spawn `resolve-pr-issue` via ciWatchLoop | `branch` | CI red; ciWatchLoop spawns resolve-pr-issue, fixes and pushes |
| `pr.reviewComment` | `PRInput` | spawn `resolve-pr-issue` via commentResolutionLoop | `branch` | Unresolved review thread; commentResolutionLoop spawns resolve-pr-issue, addresses and resolves |
| `pr.unfixable` | `PRInput` | `StandardError` | `error` | resolve-pr-issue returns fixed: false or max iterations exceeded; pr-agent reports error |

---

### Flow: `repair`

- Core files: `agents/dark-factory/agents/repair-agent.md`, `agents/repair/agents/repair-agent.md`

#### Types

```txt
RepairWorkerInput {
  taskDescription: string (verbatim user request — what to fix or change)
}

RepairImplementationOutput {
  success: boolean
  significantChange: boolean  -- true if change touches agents, skills, commands, or public APIs
  error?: StandardError
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `repair.success` | `RepairWorkerInput` | `RepairImplementationOutput{success: true}` | `happy path` | change applied, tests pass; repair-agent returns to orchestrator; orchestrator handles code review, docs, skills, PR, cleanup |
| `repair.implementation-failure` | `RepairWorkerInput` | `StandardError` | `error` | repair-agent returns success=false after 5 retries; repair-agent reports error; orchestrator runs cleanup |

---

### Flow: `brain-hooks`

- Core files: `agents/dark-factory/scripts/pre-tool-use-hook.sh`, `agents/dark-factory/scripts/post-tool-use-hook.sh`, `.claude/settings.json`

#### Types

```txt
HookPhaseEvent {
  hook:  "pre-tool-use-hook" | "post-tool-use-hook"
  phase: string   (e.g. "worker", "docs", "pr")
  event: "set-phase-running" | "set-phase-complete" | "inject" | "merge-patch" | "no-brain" | "no-patch"
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `brain-hooks.pre-inject` | Agent tool call + brain.json | modified Agent prompt with brain state prepended | happy path | pre-tool-use-hook reads brain.json, prepends it to the agent prompt, sets current phase *-running=true |
| `brain-hooks.pre-no-brain` | Agent tool call (no brain.json) | pass-through unchanged | happy path | DARK_FACTORY_WORK_DIR unset or brain.json absent — not a dark-factory session |
| `brain-hooks.post-merge` | brain-patch.json + brain.json | brain.json updated, brain-patch.json deleted | happy path | post-tool-use-hook merges patch fields into brain.json using jq -s merge |
| `brain-hooks.post-no-patch` | (no brain-patch.json) | brain.json phase flag updated only | happy path | sub-agent wrote no patch; only *-running=false and *-complete=true set |
| `brain-hooks.post-no-brain` | (no brain.json) | exit 0 silently | happy path | not a dark-factory session |

#### Pseudocode

```
pre-tool-use-hook.sh (fires before every Agent tool call):
  if DARK_FACTORY_WORK_DIR unset or brain.json absent: pass stdin through, exit 0
  PHASE = first phase in brain.json where -running=false and -complete=false
  if PHASE found: set brain.json.phases["<PHASE>-running"] = true
  prepend brain.json content to the Agent prompt (stdout = modified tool input JSON)

post-tool-use-hook.sh (fires after every Agent tool call):
  if DARK_FACTORY_WORK_DIR unset or brain.json absent: exit 0
  if brain-patch.json exists: jq -s merge brain.json + brain-patch.json → brain.json; rm brain-patch.json
  RUNNING_PHASE = phase where *-running=true in brain.json
  if RUNNING_PHASE found: set *-running=false, set *-complete=true in brain.json
```

#### Sub-agent contract

Every sub-agent that produces output fields writes `$DARK_FACTORY_WORK_DIR/brain-patch.json` with only its output fields:

| Sub-agent | Patch fields written |
|---|---|
| feature-agent (via planning-agent / sub-planning-agent) | `planFilePath` |
| debugger-agent | `bugFiles` |
| update-documentation-agent | `docsWritten` |
| skill-update-agent | `skillsWritten` |
| pr-agent | `prUrl` |

Rules:
- Sub-agents MUST NOT read brain.json directly — context is injected by pre-hook.
- Sub-agents MUST NOT write brain.json directly — only write brain-patch.json.
- Sub-agents MUST NOT set phase flags — hooks own those.
- brain-patch.json is deleted by post-tool-use-hook.sh after merge.

---

## Logs

| Source | Location |
|--------|----------|
| Agents (general) | Claude Code session transcript — agents produce no structured runtime log files |
| pre-tool-use-hook.sh | stderr (phase-running events, inject confirmation); stdout reserved for modified tool input |
| post-tool-use-hook.sh | stderr (merge-patch events, phase-complete events) |
| brain.json | `$DARK_FACTORY_WORK_DIR/brain.json` — live state readable during any run; deleted on cleanup |

## Deployment

- Mechanism: `local only`
- Deploy command:
  ```bash
  # Agents are loaded by the Claude Code runtime from the plugin directory.
  # No deployment step — install the plugin with:
  claude plugin install dark-factory
  ```
- Notes: Agents run inside Claude Code sessions on the developer's local machine. There is no remote runtime or server.

## Front-matter Conventions

Every agent file has a YAML front-matter block:

| Field | Purpose |
|---|---|
| `name` | Agent identifier |
| `user-invocable` | Whether the agent can be invoked directly by the developer |
| `description` | One-line summary shown in Claude Code |
| `tools` | Comma-separated list of Claude tools the agent may use |
| `model` | Model to use (`haiku` for pure orchestrators, `sonnet` for workers) |
| `skills` | Skill files the agent references |
| `allowed-tools` | Fine-grained bash command allowlist |
| `scripts` | Shell scripts the agent is permitted to run |

### Model Assignment

Agents are split into two tiers based on whether they perform deep reasoning:

**Orchestrators — `model: haiku`** (route, sequence, and delegate; no code/plan/doc writing):

| Agent | Role |
|---|---|
| `dark-factory-agent` | Classifies task, preps work dir, routes to worker, coordinates cleanup |
| `planning-agent` | Pure phase-delegator; spawns sub-planning-agent per phase |
| `feature-agent` | Drives phase-by-phase planning gate; calls planning-agent and execution-agent |
| `execution-agent` | Sequences skeleton → testing → implementation agents; gate-checks checklists |
| `code-review-orchestrator-agent` | Creates issues.md, spawns parallel reviewers, runs resolver loop |
| `fix-flow-orchestrator` | Sequences investigation → setup-wizard → ralph-fix-and-push; no debugging |
| `ralph-fix-and-push` | Loops: debugger-agent → pr-agent → deploy; no debugging or PR work itself |

**Workers — `model: sonnet`** (write code, plans, docs, tests, or perform deep reasoning/debugging/review):

| Agent | Role |
|---|---|
| `sub-planning-agent` | Researches codebase, writes plan files, runs mermaid scripts |
| `skeleton-agent` | Reads plan, builds files checklist, creates skeleton files |
| `testing-agent` | Reads plan, builds flows checklist, writes failing tests |
| `implementation-agent` | Implements each flow from checklist, runs tests, invokes deviation-protocol |
| `high-level-review-agent` | Reviews code against plan for structural/architectural conformance |
| `low-level-review-agent` | Reviews code at function level for bugs, untested paths, conflicts |
| `resolver-agent` | Reads issues, applies fixes, checks them off |
| `debugger-agent` | Systematic debugging following debug skill checklist |
| `detect-drift-agent` | Audits parity between docs and code, fixes drift in place |
| `investigation-agent` | Returns existing `docs/docs/` immediately (treated as authoritative); if none exist, explores codebase and creates new docs |
| `update-documentation-agent` | Identifies affected flows/docs, updates/adds sections |
| `debug-flow-agent` | Runs integration flow, waits, fetches logs, hands off to debugger-agent |
| `setup-wizard` | Reads system document, generates trigger/wait/fetch-logs/deploy scripts |
| `pr-agent` | Manages full PR lifecycle: build body, open PR, CI watch loop, comment resolution |
| `resolve-pr-issue` | Resolves single PR issue (CI failure or review thread) |
| `repair-agent` | Applies targeted changes, runs test suite, iteratively fixes failures |
| `skill-update-agent` | Reviews completed work, identifies patterns, writes/updates skill files |

Agents that call `PushNotification` in their body must declare it in `tools:` — the Claude Code runtime silently skips notifications for agents missing this declaration (see `docs/bugs/2026-04-25-push-notification-missing-from-tools.md`).

## Investigation Agent Pattern

Worker agents delegate system-understanding work to `investigation-agent` rather than performing their own code research. This is the single-responsibility convention for documentation generation. Guidance is injected globally via `CLAUDE.md` so all agents receive it automatically.

### When to invoke investigation-agent

- Before making code changes to a system you don't fully understand
- Before writing tests for a system
- When planning changes that may affect other parts of the codebase
- When you need to understand component interactions or system architecture

### How investigation-agent behaves

1. Checks `docs/docs/<system-name>.md` for existing documentation.
2. If docs exist — returns them immediately. Existing docs are treated as authoritative; no staleness check is performed.
3. If no docs exist — uses `skills/investigate/SKILL.md` to explore the codebase, then writes `docs/docs/<system-name>.md` using `skills/documentation/SKILL.md`.
4. Returns the documentation content and file path to the caller.

### Caller contract

```
result = invoke investigation-agent({
  system: "<system-name>",
  question: "<specific question or blank for general overview>"
})

if result.error:
  log("doc lookup failed for " + system + ", continuing with partial knowledge")
  # continue with best effort — do not block on investigation failures
else:
  # use result.content to inform your work
```

Drift detection is a separate concern owned by `detect-drift-agent`, not `investigation-agent`.
