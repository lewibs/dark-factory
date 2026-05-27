---
name: worker-agent-short-circuit-flag
description: "How to add a boolean flag to a worker agent so a calling orchestrator can stop it before its final execution phase and receive a return value early."
user-invocable: false
---
## When to use

When a worker agent has multiple sequential phases and you want a caller to be able to stop it after an intermediate phase rather than letting it run to completion. The canonical example is `feature-agent` receiving `planOnly: true` to stop after plan approval and return `planPath` before calling `execution-agent`.

Use this when:
- A worker agent's final phase (e.g., execution, deployment, commit) should be optional
- Multiple commands reuse the same worker but need different stopping points
- You want to avoid duplicating the worker's logic in a new agent

## Steps

1. Add the flag to the worker agent's input type documentation:
   ```
   FeatureAgentInput {
     taskDescription: string | null
     answer:          string | null
     planPath:        string | null
     planOnly:        boolean   # NEW — default false; when true, skip execution-agent
   }
   ```

2. In the worker agent's pseudocode, add the short-circuit immediately after the last phase the caller wants to observe — before the phase the caller wants to skip:
   ```
   # ── Phase 4: Final Approval Gate ────────────────────────
   # ... existing gate logic ...

   if answer == "Abort":
     RETURN { status: "aborted", reason: "User aborted", planPath }

   # ── NEW: short-circuit for planOnly callers ──────────────
   if planOnly == true:
     RETURN { status: "done", planPath }

   # ── Phase 5: Execute (only when planOnly == false) ───────
   invoke execution-agent({ planPath })
   ```

3. In the calling orchestrator, always pass the flag explicitly:
   ```
   result = invoke feature-agent({ taskDescription, planOnly: true, ... })
   ```
   On subsequent loop iterations (when the agent returns `status: "question"`), re-pass the flag:
   ```
   result = invoke feature-agent({ answer, planPath: result.planPath, planOnly: true })
   ```

4. The return value when the flag triggers must include all output the caller needs (`planPath`, etc.). The caller reads these directly from the return value — no brain.json or side-channel file is needed.

## Notes

- Default the flag to `false` so existing callers that do not pass it get unchanged behavior.
- The flag must be re-passed on every invocation inside a retry/question loop — it is not persisted between agent invocations.
- Do not add the short-circuit before any user-facing gate (e.g., "Approve and Execute") — the gate must still fire so the user can abort. Place the short-circuit after the gate check and before the skipped phase.
- If the worker uses brain.json or brain-patch.json, the short-circuit path must still write any output fields the caller reads. With the stateless direct-return pattern, this is not an issue — just include all needed fields in the RETURN object.
