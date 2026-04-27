---
name: phase-enum-sub-agent
description: "How to implement a single worker sub-agent that accepts a phase enum to handle multiple distinct jobs, avoiding proliferation of narrow one-job sub-agents."
user-invocable: false
---
## When to use

When an orchestrator needs to dispatch work across several sequential phases (e.g., draft, diagram, flows) and each phase does a different type of work (research+write, run-script, edit-section), instead of creating a separate agent file per phase, create one worker agent that branches on a `phase` input field.

Use this when:
- There are 2–5 phases, each with a distinct action but sharing a common artifact (e.g., a plan file path).
- The phases are always executed by the same orchestrator in the same order.
- You want one AGENT_CHECKLISTS entry and one agent `.md` file to maintain.

Do NOT use this if phases require fundamentally different tools lists (e.g., one phase needs network access that others must not have) — in that case, separate agents with separate `tools:` declarations are safer.

## Steps

1. **Define a Phase enum in the plan's Global Types section:**
   ```
   Phase = "phase_a" | "phase_b" | "phase_c"
   ```

2. **Define a single WorkerInput type with `phase` as required:**
   ```
   WorkerInput {
     phase: Phase (required)
     artifactPath: string | null  (null on first call of phase_a)
     feedback: string             (user feedback or "none")
     <phase-specific fields>: string | null  (null when not applicable)
   }
   ```

3. **In the worker agent `.md`, branch explicitly on `phase` at the top level:**
   ```
   ## Phase: phase_a
   When phase == "phase_a": ...

   ## Phase: phase_b
   When phase == "phase_b": ...

   ## Phase: phase_c
   When phase == "phase_c": ...
   ```
   Do not use if/else chains inside a single section — one `##` heading per phase keeps the agent prompt scannable.

4. **Each phase section must stand alone** — it should not reference state from a previous phase invocation. The orchestrator passes all needed context through `WorkerInput` each time.

5. **Define a unified WorkerOutput that covers all phases:**
   ```
   WorkerOutput {
     artifactPath: string         (always present — path to written/updated artifact)
     url: string | null           (only for phases that produce a URL; null otherwise)
     summary: string              (always present — short description of what was done)
   }
   ```
   Use `null` for fields that don't apply to a given phase rather than omitting them — this keeps the orchestrator's parsing logic simple.

6. **Pass phase-specific fields as null when not applicable.** For example, if only `phase_c` uses `flowName`, pass `flowName: null` for `phase_a` and `phase_b` invocations. Document this in the input type definition.

7. **Register one checklist entry in `pre-tool-use-hook.sh`** that covers the superset of steps across all phases:
   ```bash
   AGENT_CHECKLISTS["<worker-name>"]="Research phase context|Update artifact file|Run script (<phase_b> only)|Return structured output"
   ```

## Notes

- **The worker must always write the artifact file — never return content for the caller to save.** The worker owns the file. The orchestrator only reads it after the worker has written it. This avoids a class of bugs where the caller forgets to write or writes to the wrong path.
- **`feedback: "none"` is a valid sentinel** — the worker should check `if feedback != "none": apply changes` rather than checking for null. This avoids null-handling branches in the worker prompt.
- **Keep phase sections short.** If a phase section grows beyond ~15 lines of pseudocode, consider whether it belongs in a nested sub-agent (e.g., `investigation-agent`) rather than inline in the worker.
- The canonical reference implementation is `agents/featurework/planning/agents/sub-planning-agent.md` with phases `draft_plan`, `mermaid`, and `flows`.
