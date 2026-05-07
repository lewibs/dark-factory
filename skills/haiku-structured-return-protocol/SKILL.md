---
name: haiku-structured-return-protocol
description: "When a Haiku agent must return structured JSON to its caller, add an explicit RETURN PROTOCOL comment block and an else-error branch in the caller loop — without these, Haiku frequently returns free text and the caller silently misroutes."
user-invocable: false
---
## When to use

Whenever a Haiku-model agent is expected to return a JSON object with a typed `status` field (or any other structured envelope) back to a calling agent. The common failure mode is: Haiku returns conversational prose or intermediate reasoning text instead of the expected JSON, and the caller treats the unexpected output as a successful but unknown status — causing silent misrouting (e.g., falling through to the wrong sub-agent).

Concretely, apply this skill when:
- A Haiku agent has a multi-phase or multi-turn protocol and must return `{ status: "done" | "question" | "hard-stop" | "aborted" }`.
- A calling agent loops on a Haiku worker's return value and branches on `result.status`.
- You see any case statement or if-chain in an orchestrator that handles only the _expected_ statuses without an explicit else/default error branch.

## Steps

### In the worker agent (Haiku)

1. At the top of the `## Orchestration` section (before the pseudocode block), add both an ASCII-box banner (for maximum visual salience) AND a plain-comment reinforcement line. The banner format is more effective than a plain comment alone — Haiku is more likely to respect a visually prominent constraint block:
   ```
   # ┌─────────────────────────────────────────────────────────────────────────────┐
   # │ CRITICAL: JSON RETURN PROTOCOL (NON-NEGOTIABLE)                             │
   # │                                                                              │
   # │ This agent ALWAYS returns structured JSON. NEVER return free text.          │
   # │ EVERY response to the caller must be valid JSON with a "status" field.      │
   # │ Valid status values: "question", "done", "hard-stop", "aborted"             │
   # │                                                                              │
   # │ Allowed response structures:                                                │
   # │ - { "status": "question", "question": "...", "options": [...], ... }       │
   # │ - { "status": "done", "planPath": "..." }                                  │
   # │ - { "status": "hard-stop", "reason": "..." }                               │
   # │ - { "status": "aborted", "reason": "..." }                                 │
   # │                                                                              │
   # │ VIOLATIONS: returning conversational text, raw markdown, error strings      │
   # │ without JSON wrapper, or any response that does not parse as JSON.          │
   # └─────────────────────────────────────────────────────────────────────────────┘

   # RETURN PROTOCOL: This agent ALWAYS returns structured JSON.
   # Every RETURN statement in this pseudocode must produce JSON with a "status" field.
   # Never return free text, explanations, or intermediate analysis.
   ```
   Adapt the banner's "Allowed response structures" section to enumerate the exact JSON shapes valid for the specific agent.

2. In the `## Rules` section, add:
   - `ALWAYS return structured JSON with a 'status' field. Valid statuses: <list all valid values>. Never return raw text, conversational responses, or any output that does not parse as JSON with a 'status' field.`
   - If the protocol includes a compound return (e.g., `status: "question"` with additional fields), enumerate all required fields explicitly: `When returning { status: 'question' }, ALWAYS include: question (string), options (array of strings), planPath (string or null), phase (string).`

### In the calling agent (orchestrator loop)

3. In the loop that processes the worker's return value, add a comment before the if-chain:
   ```
   # IMPORTANT: <worker-name> ALWAYS returns a JSON object with a "status" field.
   # Do NOT interpret worker output as free text. Parse it as JSON.
   ```

4. After all expected `if result.status == "..."` branches, add an explicit `else` error branch:
   ```
   else:
     # Unexpected status — treat as error (Haiku may return free text; never silently continue)
     run cleanup(WORK_DIR, taskName)
     report "worker returned unexpected status: " + result.status
     STOP
   ```
   This prevents silent fall-through to the wrong route when Haiku emits something unexpected.

## Notes

- The root cause is a Haiku model limitation: Haiku is cheaper and faster but less reliable at adhering to structured output formats compared to Sonnet. It will sometimes emit intermediate reasoning or re-explain its intent instead of emitting only JSON.
- Adding the `else` error branch in the caller is equally important as the protocol comment in the worker — without it, an unexpected string value for `result.status` evaluates to falsy and the caller silently skips all branches or falls through to a default route.
- This pattern was first identified when `dark-factory-agent` (Haiku orchestrator) was routing around `feature-agent` (also Haiku) and invoking `sub-planning-agent` directly, because `feature-agent` returned a non-JSON string and none of the `if result.status == ...` branches matched.
- If the plain-comment RETURN PROTOCOL fails (agent still returns free text), escalate to the ASCII-box banner format described in Step 1 above. The banner was added to `feature-agent` after the plain comment alone proved insufficient — Haiku paid more attention to the visually prominent constraint block.
- If the banner also fails, consider switching the worker to Sonnet (see `haiku-orchestrator-worker-split` skill for classification guidance).
- Do not rely solely on JSON schema enforcement in the tool call — Claude Code agents return text via their final assistant message, not via a tool, so schema enforcement does not apply.
