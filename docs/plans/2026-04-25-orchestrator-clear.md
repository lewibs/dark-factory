# Plan: Add /clear after cleanup in dark-factory-agent

**Date:** 2026-04-25  
**File:** `agents/dark-factory/agents/dark-factory-agent.md`

---

## Problem

After `dark-factory-agent` completes orchestration (success or error), the conversation context holds all the accumulated agent output from the run. This pollutes the context for any subsequent work the developer does in the same session. Running `/clear` after every terminal exit point (success and all error paths that call `cleanup`) resets the context so the next task starts clean.

---

## Architecture

No new agents, scripts, or files are needed. This is a pure text edit to `dark-factory-agent.md` — adding a single `/clear` invocation at each exit point that follows a `cleanup(WORK_DIR)` call.

### Exit points that require /clear

| Location in pseudocode | Trigger condition |
|---|---|
| Step 2 — worker error/hard-stop | `cleanup(WORK_DIR)` → report error → STOP |
| Step 3 — code-review error | `cleanup(WORK_DIR)` → report error → STOP |
| Step 4 — unresolvable drift items | `cleanup(WORK_DIR)` → STOP |
| Step 5 — pr-agent error/cannot merge | `cleanup(WORK_DIR)` → report error → STOP |
| Step 6 — happy path | `cleanup(WORK_DIR)` → Done message → STOP |

The prep failure in Step 1 does NOT get `/clear` because `cleanup` is never called there (the work dir was never created); this exit is intentionally excluded.

---

## Mermaid diagram

```mermaid
flowchart TD
    A[dark-factory-agent invoked] --> B[Step 1: prep-feature-dir.sh]
    B -- fail --> Z1[report error · STOP\nno cleanup · no /clear]
    B -- ok --> C[Step 2: route to worker agent]
    C -- error/hard-stop --> CL1[cleanup WORK_DIR]
    CL1 --> CL1c[/clear]
    CL1c --> Z2[report error · STOP]
    C -- ok --> D[Step 3: code-review-orchestrator-agent]
    D -- error --> CL2[cleanup WORK_DIR]
    CL2 --> CL2c[/clear]
    CL2c --> Z3[report error · STOP]
    D -- ok --> E[Step 4: update-documentation-agent + detect-drift-agent]
    E -- unresolvable items --> CL3[cleanup WORK_DIR]
    CL3 --> CL3c[/clear]
    CL3c --> Z4[report unresolved items · STOP]
    E -- ok --> F[Step 5: pr-agent]
    F -- error/cannot merge --> CL4[cleanup WORK_DIR]
    CL4 --> CL4c[/clear]
    CL4c --> Z5[report error · STOP]
    F -- ok --> G[Step 6: cleanup WORK_DIR]
    G --> Gc[/clear]
    Gc --> Z6[Done. PR URL. Work dir removed. · STOP]
```

---

## Acceptance criteria

1. After a successful run (Step 6), `/clear` is invoked immediately after `cleanup(WORK_DIR)` and before the Done message.
2. After each of the four error-exit paths (Steps 2, 3, 4, 5), `/clear` is invoked immediately after `cleanup(WORK_DIR)`.
3. The Step 1 prep failure path does NOT invoke `/clear`.
4. The `cleanup` function definition itself is NOT modified — `/clear` is called at the call sites, not inside `cleanup`.
5. No other logic, ordering, or wording in the agent is changed.

---

## Implementation

Single file to edit: `agents/dark-factory/agents/dark-factory-agent.md`

### Changes to the orchestration pseudocode block

**Step 2 error path** — change:
```
    run cleanup(WORK_DIR)
    report error and STOP
```
to:
```
    run cleanup(WORK_DIR)
    /clear
    report error and STOP
```

**Step 3 error path** — change:
```
    run cleanup(WORK_DIR)
    report error and STOP
```
to:
```
    run cleanup(WORK_DIR)
    /clear
    report error and STOP
```

**Step 4 unresolvable drift path** — change:
```
    report the unresolved items to the developer
    run cleanup(WORK_DIR)
    STOP
```
to:
```
    report the unresolved items to the developer
    run cleanup(WORK_DIR)
    /clear
    STOP
```

**Step 5 error path** — change:
```
    run cleanup(WORK_DIR)
    report error and STOP
```
to:
```
    run cleanup(WORK_DIR)
    /clear
    report error and STOP
```

**Step 6 happy path** — change:
```
  cleanup(WORK_DIR)

  Report: "Done. PR: <prUrl>. Work dir <WORK_DIR> removed."
  STOP
```
to:
```
  cleanup(WORK_DIR)
  /clear

  Report: "Done. PR: <prUrl>. Work dir <WORK_DIR> removed."
  STOP
```

---

## Files checklist

- [ ] `agents/dark-factory/agents/dark-factory-agent.md` — add `/clear` at all five exit points described above

---

## Out of scope

- No changes to `cleanup()` internals.
- No changes to any other agent or script.
- No new tests (agent markdown files are not unit-tested; correctness is validated by inspection against acceptance criteria).
