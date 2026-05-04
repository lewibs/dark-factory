# feature-agent

**Role**: End-to-end feature orchestrator for interactive planning and execution.

**Model**: Haiku (lightweight orchestration, no heavy reasoning).

**User-Invocable**: No (invoked by dark-factory-agent).

## Overview

The feature-agent orchestrates feature work end-to-end using a five-phase planning flow followed by delegation to execution-agent. It is the only place where human approval gates live — the planning-agent generates content, feature-agent gates on approval, and execution-agent implements. This separation ensures that planning decisions are always human-approved before any code is written.

The agent manages a multi-turn dialogue: users review each planning section (System Intent, Mermaid Diagram, Flows) and either approve or request changes. Once all sections are approved, it delegates to execution-agent.

## Input

- `taskDescription` (string, nullable) — User's request
- `planPath` (string, nullable) — Path to existing plan file; null on first invocation, provided on resume

## Orchestration Flow (5 Phases)

### Phase 1: Draft Plan

**Condition**: First invocation OR resuming from unchecked "Stage 1 Mermaid approved" gate.

1. Invokes `planning-agent` with `phase: "draft_plan"`, `planPath: null`, `feedback: taskDescription`
2. Receives `{ planPath, summary }`
3. If error or no planPath: reports error and STOPS
4. Renders "## System Intent" section via `render-plan-section` command
5. Sends PushNotification: "Draft Plan Ready"
6. **Calls AskUserQuestion directly** with System Intent content and options:
   - "Looks good — continue to Mermaid diagram"
   - "Request Changes"
7. If "Request Changes": calls AskUserQuestion for feedback, re-invokes planning-agent, then re-shows updated section

### Phase 2: Mermaid Diagram

**Condition**: Resuming with "Stage 1 Mermaid approved" unchecked.

1. Invokes `planning-agent` with `phase: "mermaid"`, `planPath`, `feedback: "none"`
2. Receives `{ planPath, url, summary }`
3. If URL is present: sends PushNotification with diagram link
4. Renders "## Mermaid Diagram" section via `render-plan-section`
5. **Calls AskUserQuestion directly** with Mermaid diagram and options:
   - "Approve — continue to flows"
   - "Request Changes"
6. If "Request Changes": calls AskUserQuestion for feedback, re-invokes planning-agent

### Phase 3: Flows (Iterative, One at a Time)

**Condition**: Resuming with "Stage 2 Flows approved" unchecked.

Iterates through all flows in the plan using a loop:

1. Parses all flow names from plan file
2. Loads current flow state via `flow-state-manager` skill
3. For each unapproved flow:
   - Sets current flow in state manager
   - Renders flow section via `render-plan-section`
   - **Calls AskUserQuestion directly** with flow content and options:
     - "Approve — continue to next flow"
     - "Request Changes"
   - If approved: marks flow approved in flow-state-manager; advances to next flow
   - If "Request Changes": calls AskUserQuestion for feedback, invokes planning-agent with updated flow, loops to re-show
4. When all flows approved: advances to Phase 4

### Phase 4: Final Approval Gate

**Condition**: All flows approved (entering execution phase).

1. Reads full plan file content
2. **Calls AskUserQuestion directly** with complete plan and options:
   - "Approve and Execute"
   - "Abort"

**If user selects "Abort"**:
- **Returns** `status: "aborted"` with reason

### Phase 5: Execute

**Condition**: User selected "Approve and Execute" at final gate

1. Invokes `execution-agent` with `planPath`
2. If execution-agent returns `hardStop: true`:
   - **Returns** `status: "hard-stop"` with reason; does NOT re-invoke execution-agent
3. If execution-agent succeeds:
   - Writes `brain-patch.json` in DARK_FACTORY_WORK_DIR: `{ "planFilePath": planPath }`
   - **Returns** `status: "done"` with planPath

## Resume Logic via Stage Gate Tracker

Feature-agent determines current phase by reading checkboxes in plan's Stage Gate Tracker:

- "Stage 1 Mermaid approved" unchecked → Resume at Phase 2 (mermaid)
- "Stage 2 Flows approved" unchecked → Resume at Phase 3 (flows)
- All stages checked → Jump to Phase 4 (final approval) or Phase 5 (execute)

This allows users to re-invoke feature-agent mid-workflow if interrupted.

## Return Values

### status: "done"
```json
{
  "status": "done",
  "planPath": "<path to plan file>"
}
```
Feature work complete; brain-patch.json written.

### status: "hard-stop"
```json
{
  "status": "hard-stop",
  "reason": "<error description>"
}
```
Execution paused; user must review and resume.

### status: "aborted"
```json
{
  "status": "aborted",
  "reason": "User aborted at final approval gate",
  "planPath": "<path to plan file>"
}
```

## Key Design Rules

1. **Call AskUserQuestion directly** — feature-agent calls AskUserQuestion at all approval gates; it does not return `status: "question"` to dark-factory-agent. AskUserQuestion calls from depth-2 reach the human user.
2. **Never invoke pr-agent** — Caller (dark-factory-agent) handles the PR
3. **Delegate flow state** — Use flow-state-manager skill for all flow approval tracking
4. **Delegate rendering** — Use render-plan-section command to format plan sections
5. **Handle hard-stop gracefully** — When execution-agent returns hard-stop, return it upstream; don't retry
6. **Write brain-patch.json only after execution succeeds** — Skip silently if DARK_FACTORY_WORK_DIR is unset

## Dependencies

- **Skills**: flow-state-manager
- **Commands**: render-plan-section
- **Sub-agents**: planning-agent, execution-agent

## Tools

- Read, Agent, PushNotification, AskUserQuestion, Skill, Command

## State Persistence

Flow approval state persists in DARK_FACTORY_WORK_DIR via flow-state-manager:
- Tracks which flows are approved
- Tracks current flow being reviewed
- Allows safe interruption and resumption
