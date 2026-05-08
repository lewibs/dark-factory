# feature-agent

**Role**: End-to-end feature orchestrator for interactive planning and execution.

**Model**: Haiku (lightweight orchestration, no heavy reasoning).

**Prompt Caching**: Yes — `cache-control: ephemeral` is set in YAML frontmatter. Claude Code applies prompt caching when spawning this agent, reducing system prompt token costs by ~90% for repeated invocations.

**User-Invocable**: No (invoked by dark-factory-agent).

## Overview

The feature-agent orchestrates feature work end-to-end using a five-phase planning flow followed by delegation to execution-agent. It is the only place where human approval gates live — the planning-agent generates content, feature-agent gates on approval, and execution-agent implements. This separation ensures that planning decisions are always human-approved before any code is written.

The agent runs at depth 2 (dark-factory-agent → feature-agent) and calls `AskUserQuestion` directly for all user interaction. It does NOT return `status: "question"` to the caller — it handles all approval loops internally in a single invocation. dark-factory-agent invokes feature-agent once and waits for a terminal status.

## Input

- `taskDescription` (string) — User's request

## Orchestration Flow (5 Phases)

### Phase 1: Draft Plan

1. Invokes `planning-agent` with `phase: "draft_plan"`, `planPath: null`, `feedback: taskDescription`
2. Receives `{ planPath, summary }`
3. If error or no planPath: returns `{ status: "hard-stop", reason: "..." }`
4. Renders "## System Intent" section via `render-plan-section` command
5. Sends PushNotification: "Draft Plan Ready"
6. **Calls AskUserQuestion directly** with System Intent content and options:
   - "Looks good — continue to Mermaid diagram"
   - "Request Changes"
7. If "Request Changes": re-invokes planning-agent with feedback and loops until approved

### Phase 2: Mermaid Diagram

1. Invokes `planning-agent` with `phase: "mermaid"`, `planPath`, `feedback: "none"`
2. Receives `{ planPath, url, summary }`
3. If URL is present: sends PushNotification with diagram link
4. Renders "## Mermaid Diagram" section via `render-plan-section`
5. **Calls AskUserQuestion directly** with Mermaid diagram and options:
   - "Approve — continue to flows"
   - "Request Changes"
6. If "Request Changes": re-invokes planning-agent with feedback and loops until approved

### Phase 3: Flows (Iterative, One at a Time)

Iterates through all flows in the plan, one per AskUserQuestion call:

1. Parses all flow names from plan file
2. Resolves `WORK_DIR` from `$DARK_FACTORY_WORK_DIR`, falling back to `/tmp/dark-factory-work-dir`
3. For each flow:
   - Sets current flow via `flow-state-manager`
   - Renders flow section via `render-plan-section`
   - **Calls AskUserQuestion directly** with flow content and options:
     - "Approve — continue to next flow"
     - "Request Changes"
   - If "Request Changes": re-invokes planning-agent for the flow with feedback and loops until approved
   - If approved: marks flow as approved in `flow-state-manager` and advances to next flow

### Phase 4: Final Approval Gate

1. Reads full plan file content
2. **Calls AskUserQuestion directly** with complete plan and options:
   - "Approve and Execute"
   - "Abort"
3. If "Abort": **Returns** `status: "aborted"` with reason

### Phase 5: Execute

1. Invokes `execution-agent` with `planPath`
2. If execution-agent returns `hardStop: true`:
   - **Returns** `status: "hard-stop"` with reason; does NOT re-invoke execution-agent
3. If execution-agent succeeds:
   - Writes `brain-patch.json` resolving work dir via pointer file fallback: `{ "planFilePath": planPath }`
   - **Returns** `status: "done"` with planPath

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

1. **Call AskUserQuestion directly for all user interaction** — feature-agent runs at depth 2; AskUserQuestion calls reach the human user directly. Never return `status: "question"` to the caller.
2. **Single invocation contract** — dark-factory-agent invokes feature-agent exactly once. All approval loops are handled internally.
3. **Never invoke pr-agent** — Caller (dark-factory-agent) handles the PR
4. **Delegate flow state** — Use flow-state-manager skill for all flow approval tracking
5. **Delegate rendering** — Use render-plan-section command to format plan sections
6. **Handle hard-stop gracefully** — When execution-agent returns hard-stop, return it upstream; don't retry
7. **Write brain-patch.json only after execution succeeds** — Resolve WORK_DIR from `$DARK_FACTORY_WORK_DIR`, then fall back to contents of `/tmp/dark-factory-work-dir`; skip silently if both are empty
8. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase
9. **ALWAYS return structured JSON** — Every return path must produce `{ status: "..." }`. Valid statuses: `done`, `hard-stop`, `aborted`. Never return free text or intermediate analysis.

## Dependencies

- **Skills**: flow-state-manager
- **Commands**: render-plan-section
- **Sub-agents**: planning-agent, execution-agent

## Tools

- Read, Write, Agent, PushNotification, Skill, Command, AskUserQuestion

## State Persistence

Flow approval state persists in DARK_FACTORY_WORK_DIR via flow-state-manager:
- Tracks which flows are approved
- Tracks current flow being reviewed
- Allows safe interruption and resumption
