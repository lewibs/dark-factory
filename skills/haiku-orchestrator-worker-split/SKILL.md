---
name: haiku-orchestrator-worker-split
description: "How to split a monolith agent into a cheap Haiku orchestrator (state, display, user interaction only) and a Sonnet worker (all research, writing, and heavy reasoning) to reduce cost and improve cognitive separation."
user-invocable: false
---
## When to use

Use this pattern when:
- A single agent is growing expensive because it both reasons heavily AND blocks on user interaction (paying Sonnet tokens for idle wait time).
- An agent mixes responsibilities: user-facing display/questioning AND heavy codebase research or file writing.
- You want to preserve an existing agent's external interface (input/output contract) while restructuring its internals.
- You are auditing an existing multi-agent system to ensure all agents are on the correct model tier (see Auditing Existing Agents below).

The canonical example is `planning-agent` (Haiku orchestrator) + `sub-planning-agent` (Sonnet worker).

## Steps

1. **Define the split boundary clearly before writing any code.**
   - Orchestrator responsibilities: TodoWrite, read files to extract sections, display content inline, call AskUserQuestion, call PushNotification, track phase state, return final output to caller.
   - Worker responsibilities: read codebase, write or edit files, run scripts (Bash), spawn further sub-agents (investigation-agent, etc.), return structured output.
   - Rule: orchestrator never uses Write, Edit, or Bash. Worker never uses AskUserQuestion or PushNotification.

2. **Define a shared structured input type for the worker** (see `phase-enum-sub-agent` skill for the multi-phase pattern):
   ```
   WorkerInput {
     phase: string         (what the worker should do this invocation)
     <artifact path>: string | null  (null on first call)
     feedback: string      (user feedback or initial description)
     <phase-specific fields>: ...
   }

   WorkerOutput {
     <artifact path>: string
     <optional fields>: ...
     summary: string
   }
   ```

3. **Set models in agent frontmatter explicitly.**
   - Orchestrator: `model: haiku`
   - Worker: `model: sonnet` (or omit to use default)
   - Declare `tools:` lists strictly — orchestrator does NOT list Write, Edit, Bash; worker does NOT list AskUserQuestion, PushNotification.

4. **Preserve the external interface.** The caller of the orchestrator sees no change: same input type, same output type. The orchestrator wraps the split internally.

5. **Register the worker in `pre-tool-use-hook.sh` AGENT_CHECKLISTS** so it gets a TodoWrite checklist injected on spawn. Add an entry like:
   ```bash
   AGENT_CHECKLISTS["<worker-name>"]="Research phase context|Update plan file|Run script (phase X only)|Return structured output"
   ```
   Update the orchestrator's checklist to reflect its new orchestrator duties instead of its old monolith duties.

6. **Orchestrator loop pattern** — for each phase where the developer can request changes:
   ```
   LOOP:
     spawn worker(phase=<phase>, artifact=<path>, feedback=<feedback or "none">)
     receive worker output
     (optionally push notification if output contains a URL)
     read artifact, extract relevant section
     display section to developer via AskUserQuestion
     if approved: BREAK
     else: feedback = developer input; CONTINUE
   ```

7. **Worker reads its own artifact on every invocation** — never trust that state from a previous invocation is in memory. The worker always reads the file at `<artifact path>` before modifying it.

## Auditing Existing Agents

When adding new agents or doing a cost-reduction pass, audit all agents in the system using a classification table. For each agent, answer:

| Question | Orchestrator (haiku) | Worker (sonnet) |
|---|---|---|
| Does it write or edit files? | No | Yes |
| Does it run Bash commands? | No | Yes |
| Does it do codebase research or deep analysis? | No | Yes |
| Does it write plans, code, docs, or tests? | No | Yes |
| Does it spawn sub-agents and only pass results through? | Yes | Rarely |
| Does it sequence phases or manage a loop without reasoning about what's inside? | Yes | No |
| Does it use AskUserQuestion or PushNotification as its primary user-facing tool? | Yes | No |

**Classification heuristics:**
- If an agent's job is "call agent A, then agent B, then agent C and return" with no content reasoning — it is an orchestrator; use haiku.
- If an agent reads logs, interprets failures, writes anything, or makes decisions based on content — it is a worker; use sonnet.
- Borderline case: an agent that reads logs AND delegates debugging to another agent. Apply the "does it interpret content to make a decision?" test. If yes, keep sonnet.

**Audit workflow:**
1. List all agent `.md` files in the codebase.
2. For each agent, read its instructions to classify as orchestrator or worker using the table above.
3. Build a classification table in the plan with columns: Agent | File | Current Model | Classification | Justification | Action.
4. For agents where Current Model does not match Classification, change only the `model:` field in YAML front-matter.
5. No logic, instruction, or tooling changes are needed — model is purely a front-matter field.

## Notes

- **Do not spawn the worker on initial display.** If the orchestrator is about to ask "approve or request changes?", read the existing artifact and show it first. Only spawn the worker when the developer has provided feedback that requires a change. Exception: the very first call in a phase (before any artifact exists) always spawns the worker to produce the initial artifact.
- **"none" as a sentinel for no feedback** — use the string `"none"` rather than null for `feedback` when there is no user input, so the worker can branch on it without null-handling.
- **Haiku cannot do deep reasoning reliably.** If you accidentally put research or multi-step reasoning into the orchestrator, it will produce lower-quality results than expected. Keep the orchestrator prompt short and mechanical.
- **The external interface must not change.** The feature-agent (or other caller) must not need to be updated when you apply this split. Validate this by checking all callers of the agent being restructured.
- The `pre-tool-use-hook.sh` brain injection still reaches the worker because the hook fires on every Agent tool call regardless of which agent spawned it.
