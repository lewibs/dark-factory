# build-feature

## Metadata

- System type: `flow`

## System Intent

- What this is: The end-to-end feature-building flow. Orchestrates planning (with Mermaid diagram, typed I/O contracts, and per-flow pseudocode), a human approval gate with feedback-and-retry, and then full execution (skeleton → tests → implementation). Does not open a PR itself — that is the caller's responsibility after documentation agents complete.

## Mermaid Diagram

```mermaid
flowchart TD
  Input["feature-agent(description)"] --> PA["planning-agent\n(Haiku orchestrator)"]
  PA -->|phase=draft_plan| SPA["sub-planning-agent\n(Sonnet worker)"]
  SPA -->|planPath + summary| PA
  PA -->|AskUserQuestion: draft review| Dev([Developer])
  Dev -->|feedback| PA
  Dev -->|approve| PA

  PA -->|phase=mermaid| SPA
  SPA -->|url + summary| PA
  PA -->|PushNotification: diagram URL| Dev
  PA -->|AskUserQuestion: mermaid review| Dev
  Dev -->|feedback| PA
  Dev -->|approve| PA

  PA -->|phase=flows (one at a time)| SPA
  SPA -->|summary| PA
  PA -->|AskUserQuestion: flow review| Dev
  Dev -->|feedback| PA
  Dev -->|approve| PA

  PA -->|planPath| Input
  Input --> Gate{Developer approval\nvia feature-agent}
  Gate -->|abort| Abort["Stop"]
  Gate -->|approve| Exec["execution-agent(planPath)"]
  Exec --> Skeleton["skeleton-agent\n(creates file stubs)"]
  Skeleton --> FilesChecklist["tmp/files-checklist.md"]
  FilesChecklist --> Testing["testing-agent\n(writes failing tests)"]
  Testing --> FlowsChecklist["tmp/flows-checklist.md"]
  FlowsChecklist --> Impl["implementation-agent\n(makes tests pass)"]
  Impl -->|hardStop| Push2["PushNotification: Execution Paused"]
  Push2 --> Wait["Wait for developer to fix plan"]
  Wait --> Impl
  Impl -->|allFlowsGreen| Done["Report: Feature complete. planPath=<path>"]
```

## Flows

### Flow: `planFeature`

- Test files: `N/A`
- Core files: `agents/featurework/agents/feature-agent.md`, `agents/featurework/planning/agents/planning-agent.md`, `agents/featurework/planning/agents/sub-planning-agent.md`, `agents/featurework/planning/templates/plan-template.md`

#### Types

```txt
PlanFeatureInput {
  description: string (required — feature description passed to planning-agent)
}

PlanFeatureOutput {
  planPath: string (absolute path to the written plan file, e.g. docs/plans/2026-04-26-add-oauth.md)
}

SubPlanningAgentInput {
  phase: "draft_plan" | "mermaid" | "flows"
  planPath: string | null  (null for draft_plan phase)
  feedback: string         (user feedback or initial feature description)
  flowName: string | null  (only for flows phase)
}

SubPlanningAgentOutput {
  planPath: string (absolute path to the written/updated plan file)
  url: string | null (mermaid.ink URL; only for mermaid phase)
  summary: string (short description of what was done)
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `planFeature.draftApproved` | `PlanFeatureInput` | proceeds to mermaid phase | happy path | planning-agent (Haiku) spawns sub-planning-agent (Sonnet) with phase=draft_plan; worker researches codebase (optionally via investigation-agent), creates plan file from template; orchestrator reads System Intent section, shows developer via AskUserQuestion |
| `planFeature.mermaidApproved` | planPath from draft | proceeds to flows phase | happy path | orchestrator spawns sub-planning-agent with phase=mermaid; worker updates diagram section and runs `python3 scripts/mermaid_to_image.py`; orchestrator pushes diagram URL via PushNotification if url is non-null |
| `planFeature.flowsApproved` | planPath | `PlanFeatureOutput` | happy path | orchestrator iterates each `### Flow:` section one at a time, shows developer, collects feedback if needed, re-spawns sub-planning-agent with phase=flows for updates; returns planPath after all flows approved |
| `planFeature.phaseRetry` | any phase | revised content | loop | developer provides feedback during any phase; orchestrator re-spawns sub-planning-agent for that phase |
| `planFeature.error` | `PlanFeatureInput` | `StandardError` | error | sub-planning-agent fails to complete a phase |

### Flow: `approveFeature`

- Core files: `agents/featurework/agents/feature-agent.md`

#### Types

```txt
ApproveFeatureInput {
  planPath: string (path to the plan file displayed to the developer)
}

ApproveFeatureOutput {
  approved: true
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `approveFeature.approved` | `ApproveFeatureInput` | `ApproveFeatureOutput` | happy path | developer replies "yes" or "approve" |
| `approveFeature.feedback` | `ApproveFeatureInput` | feedback string | retry | developer provides revision text; feature-agent loops back to planning-agent |
| `approveFeature.abort` | `ApproveFeatureInput` | stopped | user abort | developer replies "abort" |

### Flow: `executeFeature`

- Test files: `tests/`
- Core files: `agents/featurework/execution/agents/execution-agent.md`, `agents/featurework/execution/agents/skeleton-agent.md`, `agents/featurework/execution/agents/testing-agent.md`, `agents/featurework/execution/agents/implementation-agent.md`

#### Types

```txt
ExecuteFeatureInput {
  planPath: string (required — path to approved plan file)
}

ExecuteFeatureOutput {
  allFlowsGreen: true
}

HardStop {
  hardStop: true
  reason: string
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `executeFeature.success` | `ExecuteFeatureInput` | `ExecuteFeatureOutput` | happy path | skeleton → tests → implementation all pass; tmp checklists deleted |
| `executeFeature.hard-stop` | `ExecuteFeatureInput` | `HardStop` | paused | implementation-agent encounters unresolvable deviation; developer must edit plan and resume |
| `executeFeature.plan-not-found` | `ExecuteFeatureInput` | `StandardError` | error | plan file does not exist |

#### Pseudocode

```
execution-agent(planPath):
  read planPath (error if missing)

  # Stage 1: skeleton
  skeleton-agent(planPath)
  assert tmp/files-checklist.md fully checked
  assert all listed files exist on disk

  # Stage 2: tests
  testing-agent(planPath)
  assert tmp/flows-checklist.md exists
  assert all new tests are FAILING (red-green discipline)

  # Stage 3: implementation
  implementation-agent(planPath, tmp/flows-checklist.md)
  if hardStop: PushNotification, pause, wait for developer (deviation-protocol updates diagram via skills/create-mermaid-diagram/SKILL.md if architecture changed), re-run implementation-agent
  if allFlowsGreen:
    rm tmp/files-checklist.md
    rm tmp/flows-checklist.md
    report success
```

## Logs

| Source | Location |
|--------|----------|
| planning-agent output | docs/plans/<date>-<slug>.md |
| test results | Claude Code session transcript |
| checklists | tmp/files-checklist.md, tmp/flows-checklist.md (deleted on success) |

## Deployment

- Mechanism: `local only` — invoked as a sub-agent by dark-factory-agent
- Notes: feature-agent is not user-invocable directly; it is spawned by dark-factory-agent when the task classification is "new feature". The PR is opened by the caller (dark-factory-agent) after update-documentation-agent completes.
