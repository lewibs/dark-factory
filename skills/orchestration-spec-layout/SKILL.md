---
name: orchestration-spec-layout
description: "Critical execution constraints (Non-Stop Execution, JSON return protocol, tool restrictions) must appear at the TOP of an agent's spec — Haiku stops after completing a logical unit and never reads constraints placed at the bottom."
user-invocable: false
---
## When to use

Apply whenever writing or editing an agent spec (`.md` file) that contains critical behavioral constraints — especially:
- Non-Stop Execution rules (agent must not pause or stop mid-orchestration)
- JSON return protocol banners
- Tool restriction rules
- Any rule whose violation causes silent failure or premature termination

## Steps

1. **Place all critical execution constraints at the top of the spec, before any task description or orchestration pseudocode.**
   - The correct order is:
     1. YAML frontmatter (model, tools, description)
     2. Critical execution constraints block (Non-Stop Execution, return protocol, etc.)
     3. Task description / context
     4. Orchestration pseudocode
     5. Rules / notes

2. **Use a visually prominent banner for Non-Stop Execution rules.**
   ```
   # ┌─────────────────────────────────────────────────────────────────┐
   # │ NON-STOP EXECUTION (MANDATORY)                                  │
   # │                                                                  │
   # │ This agent MUST NOT stop, pause, or return control to the       │
   # │ caller until the entire orchestration is complete.              │
   # │ Never stop after completing a single phase or logical unit.     │
   # └─────────────────────────────────────────────────────────────────┘
   ```

3. **Never place Non-Stop Execution rules only at the bottom of the spec.**
   - Haiku reads the spec top-to-bottom and stops after the first complete logical unit it identifies (e.g., after spawning a sub-agent and receiving output).
   - A rule at the bottom is never reached if the agent terminates early.

4. **Audit existing specs when agents terminate prematurely.**
   - If an agent stops mid-flow without error, check whether its spec has any non-stop or continuation rules.
   - If those rules exist but are near the bottom, move them to the top.

## Notes

- This failure mode is specific to smaller/cheaper models (Haiku) that treat task completion as a natural stopping point. Sonnet is more likely to continue reading and following the full spec, but the top-placement rule is still best practice for all agents.
- The symptom of a misplaced Non-Stop rule is an agent that completes one phase correctly and then stops — returning to the caller with a partial result rather than continuing to the next phase.
- Related: `haiku-structured-return-protocol` describes a similar top-placement requirement for JSON return protocol banners — the same underlying reason applies to both.
