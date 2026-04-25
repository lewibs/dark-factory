---
name: logging-standards
description: Focused logging standards for frontend and backend. Use when adding/changing logging to enforce shared flow/step/additional format, context-scoped frontend flow usage, and test updates.
---

## Required

You must add the following steps to your implementation plan when modifying logging:

1. Use `docs/plans/logging.md` as the source of truth for logging format and behavior details.
   - API definitions and usage behavior must be documented in plan files, not only in this skill.
   - Parent contract/API: `docs/plans/logging.md`
   - Frontend API details: `docs/plans/frontend-logging.md`
   - Backend API details: `docs/plans/backend-logging.md`
2. Use shared logging utilities only:
   - Backend: `main/server/layers/shared/python/shared/logger.py` via `create_logger({flow})`
   - Frontend: `main/app/lib/logging/frontend-logger.tsx`
3. Frontend call pattern is required:
   - Log first, then call:
     - `logger({ step, additional: <input-context> })`
     - `await functionCall(payload)`
   - Do not pass logger through normal API signatures (`function(payload, logger)`).
   - Log at the flow owner boundary (screen/provider/hook) where context is known.
4. Ensure log output is structured JSON emitted by shared logging utilities.
5. Add a lot of logging, not a little:
   - log flow start and end,
   - log every meaningful step transition,
   - log user actions, branching decisions, external I/O boundaries, and errors.
6. Update tests for any logging contract or behavior changes.

## Context

Logging is intentionally verbose to improve AI debugging quality.

- **Contract**:
  - `flow`: end-to-end flow name (`auth`, `new-user`, `upload-memory`, `chat`, `memory-photos`, etc.)
  - `step`: specific step in that flow
  - `additional`: structured state/input/output context
- **Removed field**: `message` is not part of the logging contract.
- **Formatting**: All event values are stringified before logging.
- **Coverage principle**: prefer more logs rather than fewer logs.
- **Frontend flow scope**: `useLogging(...)` gets flow from `LoggingContextProvider`; do not pass flow into `useLogging`.
- **Frontend ownership**: flow-aware logs should be emitted before function calls at the owner boundary with input context in `additional`.
- **Signal quality**: avoid redundant success logs; next step-start logs imply prior success.

## Workflow

### Implementation

- Choose and keep a stable `flow` for the full flow lifetime.
- Emit a `step` log at each significant state/action boundary.
- Before each meaningful function call in a main flow, log the call input in `additional`.
- Prefer start/transition/error logs over explicit success logs.
- Keep `additional` safe: do not log secrets or sensitive personal data.

### Testing

- Backend: capture log output with `caplog` using `logger="encache"` and assert JSON contents.
- Backend: load the logger module via `spec_from_file_location` for isolated logger tests.
- Validate missing required fields, invalid types, and additional context behavior.
- Frontend: assert `useLogging` and `LoggingContextProvider` contract behavior in Jest tests.

### Updates

- When changing logging schema or flow semantics, update:
  - `docs/plans/logging.md`
  - `docs/plans/frontend-logging.md`
  - `docs/plans/backend-logging.md`
  - related tests
- Ensure the plan files explicitly capture both:
  - logging API shape (function signatures/payload contract),
  - how logging works (flow lifecycle, step boundaries, and additional context expectations).
