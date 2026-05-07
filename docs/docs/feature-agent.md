# feature-agent

**Role**: End-to-end feature orchestrator for interactive planning and execution.

**Model**: Haiku (lightweight orchestration, no heavy reasoning).

**Prompt Caching**: Yes — `cache-control: ephemeral` is set in YAML frontmatter. Claude Code applies prompt caching when spawning this agent, reducing system prompt token costs by ~90% for repeated invocations.

**User-Invocable**: No (invoked by dark-factory-agent).

## Overview

The feature-agent orchestrates feature work end-to-end using a five-phase planning flow followed by delegation to execution-agent. It is the only place where human approval gates live — the planning-agent generates content, feature-agent gates on approval, and execution-agent implements. This separation ensures that planning decisions are always human-approved before any code is written.

The agent manages a multi-turn dialogue: users review each planning section (System Intent, Mermaid Diagram, Flows) and either approve or request changes. Once all sections are approved, it delegates to execution-agent.

**Return Protocol**: This agent ALWAYS returns structured JSON with a `status` field. It never returns raw text, conversational responses, or any output that does not parse as JSON. dark-factory-agent depends on this contract to route the multi-turn loop correctly; any non-JSON output causes dark-factory-agent to halt with an error.

## Input

- `taskDescription` (string, nullable) — User's request; null on re-invocation
- `answer` (string, nullable) — User's response to a previous question; null on first invocation
- `planPath` (string, nullable) — Path to existing plan file; null on first invocation, provided on re-invocation

## Orchestration Flow (5 Phases)

### Phase 1: Draft Plan

**Condition**: First invocation OR resuming from unchecked "Stage 1 Mermaid approved" gate.

1. Invokes `planning-agent` with `phase: "draft_plan"`, `planPath: null`, `feedback: taskDescription`
2. Receives `{ planPath, summary }`
3. If error or no planPath: reports error and STOPS
4. Renders "## System Intent" section via `render-plan-section` command
5. Sends PushNotification: "Draft Plan Ready"
6. **Returns** `status: "question"` with System Intent content and options:
   - "Looks good — continue to Mermaid diagram"
   - "Request Changes"

### Phase 2: Mermaid Diagram

**Condition**: Resuming with "Stage 1 Mermaid approved" unchecked; user selected "Looks good — continue to Mermaid diagram"

1. Invokes `planning-agent` with `phase: "mermaid"`, `planPath`, `feedback: answer ?? "none"`
2. Receives `{ planPath, url, summary }`
3. If URL is present: sends PushNotification with diagram link
4. Renders "## Mermaid Diagram" section via `render-plan-section`
5. **Returns** `status: "question"` with Mermaid diagram and options:
   - "Approve — continue to flows"
   - "Request Changes"

### Phase 3: Flows (Iterative, One at a Time)

**Condition**: Resuming with "Stage 2 Flows approved" unchecked; user selected "Approve — continue to flows"

Iterates through all flows in the plan, one per turn:

1. Parses all flow names from plan file
2. Loads current flow state via `flow-state-manager` skill
3. If user answered "Approve — continue to next flow": marks current flow as approved in state manager
4. If user requested changes: invokes `planning-agent` with `phase: "flows"` and the change request
5. Finds next unapproved flow via flow-state-manager
6. If all flows approved: **GOTO Phase 4**
7. Sets current flow in state manager
8. Renders next flow section via `render-plan-section`
9. **Returns** `status: "question"` with flow content and options:
   - "Approve — continue to next flow"
   - "Request Changes"

### Phase 4: Final Approval Gate

**Condition**: All flows approved (entering execution phase) AND user hasn't yet selected "Approve and Execute"

1. Reads full plan file content
2. **Returns** `status: "question"` with complete plan and options:
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
   - Writes `brain-patch.json` resolving work dir via pointer file fallback: `{ "planFilePath": planPath }`
   - **Returns** `status: "done"` with planPath

## Resume Logic via Stage Gate Tracker

Feature-agent determines current phase by reading checkboxes in plan's Stage Gate Tracker:

- "Stage 1 Mermaid approved" unchecked → Resume at Phase 2 (mermaid)
- "Stage 2 Flows approved" unchecked → Resume at Phase 3 (flows)
- All stages checked → Jump to Phase 4 (final approval) or Phase 5 (execute)

This allows users to re-invoke feature-agent mid-workflow if interrupted.

## Return Values

### status: "question"
```json
{
  "status": "question",
  "question": "<rendered section or full plan>",
  "options": ["option1", "option2"],
  "planPath": "<path to plan file>",
  "phase": "<phase name>"
}
```
Indicates dark-factory-agent should send PushNotification and await AskUserQuestion response.

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

1. **Never call AskUserQuestion directly** — Return `status: "question"` instead; dark-factory-agent asks at depth-2
2. **Never invoke pr-agent** — Caller (dark-factory-agent) handles the PR
3. **Delegate flow state** — Use flow-state-manager skill for all flow approval tracking
4. **Delegate rendering** — Use render-plan-section command to format plan sections
5. **Handle hard-stop gracefully** — When execution-agent returns hard-stop, return it upstream; don't retry
6. **Write brain-patch.json only after execution succeeds** — Resolve WORK_DIR from `$DARK_FACTORY_WORK_DIR`, then fall back to contents of `/tmp/dark-factory-work-dir`; skip silently if both are empty
7. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase
8. **ALWAYS return structured JSON** — Every return path must produce `{ status: "..." }`. Valid statuses: `done`, `hard-stop`, `aborted`, `question`. Never return free text or intermediate analysis.
9. **status: "question" must be complete** — Always include `question` (string), `options` (array), `planPath` (string or null), and `phase` (string) when returning this status.

## Dependencies

- **Skills**: flow-state-manager
- **Commands**: render-plan-section
- **Sub-agents**: planning-agent, execution-agent

## Tools

- Read, Agent, PushNotification, Skill, Command

## State Persistence

Flow approval state persists in DARK_FACTORY_WORK_DIR via flow-state-manager:
- Tracks which flows are approved
- Tracks current flow being reviewed
- Allows safe interruption and resumption
