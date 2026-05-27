# fix-flow-orchestrator

**Role**: Autonomously drives a failing integration flow to green status.

**Model**: Haiku (lightweight orchestration, no heavy reasoning).

**User-Invocable**: No (invoked by execute-command-agent).

## Overview

The fix-flow-orchestrator is a specialized orchestrator for fixing broken integration flows. It systematically investigates the flow, generates debugging and test scripts, and loops through fix-and-push cycles until the flow passes. The flow name is required and must be provided as an argument.

## Input

- `flowName` (string, required) — Name of the failing integration flow (e.g., "login-flow", "checkout-flow")
- If not provided: sends PushNotification requesting flow name, awaits AskUserQuestion response

## Orchestration Flow (3 Phases)

### Phase 1: Understand System

**Objective**: Build system documentation and create a working plan.

1. Validates flow name is provided
   - If missing: sends PushNotification ("Input Required", "The fix-flow orchestrator needs a flow name to proceed.")
   - Uses AskUserQuestion to request flow name or allow cancel/reinvocation
   - Stops and waits for response

2. Spawns `investigation-agent` with the flow name

3. Waits for investigation-agent to return path to documentation file (in `docs/docs/`)

4. Writes `docs/plans/system-diagram.md` using the documentation as the working plan for this session

5. **Does NOT proceed to Phase 2 until** `docs/plans/system-diagram.md` exists

### Phase 2: Setup

**Objective**: Generate test trigger, log fetching, and deployment scripts.

1. Spawns `setup-wizard` sub-agent with:
   - Path to `docs/plans/system-diagram.md`

2. Waits for setup-wizard to return paths to generated scripts:
   - Trigger script
   - Fetch-logs script
   - Wait-for-completion script

3. **Does NOT proceed to Phase 3 until** all required scripts are verified to exist

### Phase 3: Fix and Push

**Objective**: Loop through fix attempts until flow passes; create single PR with all fixes.

1. Spawns `ralph-fix-and-push` sub-agent with:
   - Paths to all generated scripts from Phase 2
   - branchName (e.g., "feature/fix-flow-<flow-name>")

2. Waits for ralph-fix-and-push to complete

3. ralph-fix-and-push returns `all-green: true` when flow passes

## Completion

When ralph-fix-and-push returns `all-green: true`:

1. Reports success to developer with PR URL
2. Notes that `docs/plans/system-diagram.md` and any `docs/bugs/*.md` files are kept as persistent project documentation (not deleted)

## Key Design Rules

1. **Flow name is mandatory** — Request via AskUserQuestion if missing; do not proceed without it
2. **Strict phase sequencing** — Never advance to next phase until current phase has produced required artifacts
3. **Verify Phase 2 scripts exist** — Before invoking ralph-fix-and-push, confirm all generated scripts are present
4. **Persist documentation** — system-diagram.md and bug audit logs remain in the repository after fixes complete
5. **Single PR output** — ralph-fix-and-push produces one PR with all accumulated fixes across multiple debug loops
6. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase

## Dependencies

- **Sub-agents**: investigation-agent, setup-wizard, ralph-fix-and-push
- **Artifacts**: docs/plans/system-diagram.md (created by phase 1), generated debug scripts (created by phase 2)

## Tools

- Read, Bash, PushNotification, AskUserQuestion

## Return Value

```json
{
  "success": true,
  "prUrl": "<github PR URL>",
  "flowName": "<flow name>"
}
```

## Error Handling

- If investigation-agent fails: reports error and STOPS
- If setup-wizard fails: reports error and STOPS
- If any generated script doesn't exist: halts before Phase 3, reports error
- If ralph-fix-and-push fails: reports error (PR may still have been created)
