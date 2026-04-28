---
name: phase-agent-allowlist
description: "How to restrict phase-running/phase-complete transitions in brain.json hooks to top-level orchestration agents only, preventing nested sub-agents from corrupting the phase state machine."
user-invocable: false
---
## When to use

When the dark-factory hooks track phases (e.g., `planning-running`, `planning-complete`) AND the system invokes `Agent` or `Skill` tool calls at multiple nesting depths (e.g., feature-agent calls repair-agent calls a helper agent).

Without an allowlist, every `Agent` tool call — including deeply nested ones — triggers a phase transition. A nested agent completion can flip a phase to complete before the actual top-level agent responsible for that phase has finished, breaking the state machine.

## Steps

1. Define the allowlist as a pipe-delimited regex string in both `pre-tool-use-hook.sh` and `post-tool-use-hook.sh`:
   ```bash
   PHASE_AGENTS="feature-agent|debugger-agent|fix-flow-orchestrator|repair-agent|code-review-orchestrator-agent|update-documentation-agent|skill-update-agent|pr-agent"
   ```
   List only the top-level orchestration agents — the ones that map 1:1 to phases in `brain.json`.

2. In `pre-tool-use-hook.sh`, extract the agent name from the tool input and gate the phase-running block:
   ```bash
   PHASE_AGENT_NAME=""
   if [ "$TOOL_NAME" = "Agent" ]; then
     PHASE_AGENT_NAME=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.subagent_type // ""')
   fi

   if [[ "$PHASE_AGENT_NAME" =~ ^($PHASE_AGENTS)$ ]]; then
     # set phase *-running = true
   else
     echo "pre-tool-use-hook | set-phase-running | skipped (agent=${PHASE_AGENT_NAME} not a phase agent)" >&2
   fi
   ```

3. In `post-tool-use-hook.sh`, extract the metrics key (which equals the agent/skill name) and gate the phase-complete block:
   ```bash
   if [[ "$METRICS_KEY" =~ ^($PHASE_AGENTS)$ ]]; then
     # set phase *-running = false, *-complete = true
   else
     echo "post-tool-use-hook | set-phase-complete | skipped (agent=${METRICS_KEY} not a phase agent)" >&2
   fi
   ```
   This block must be nested inside the `if [ "$TOOL_NAME" = "Agent" ] || [ "$TOOL_NAME" = "Skill" ]` block so `METRICS_KEY` is already resolved.

4. Metrics accumulation (elapsed_ms, tokens, runs) is NOT gated — it runs for all agents and skills at all depths. Only phase transitions are restricted.

5. When adding a new top-level orchestration agent, add its `subagent_type` value to the `PHASE_AGENTS` string in both hook scripts simultaneously. Forgetting one will cause the pre-hook to start a phase but the post-hook to never complete it.

## Notes

- The `METRICS_KEY` in the post-hook is derived from `tool_input.subagent_type` for Agent calls and `tool_input.name` for Skill calls. Phase agents are always `Agent` type, so the Skill branch never triggers phase transitions by design.
- Use `^($PHASE_AGENTS)$` (anchored regex) to prevent partial matches (e.g., `repair-agent-helper` accidentally matching `repair-agent`).
- The allowlist lives in the hook scripts, not in brain.json, because it describes the hook's own behavior, not task state.
- If a phase agent is retried (called more than once), the pre-hook will attempt to advance to the next unstarted phase on the retry. Ensure retry logic in the orchestrator accounts for this, or make the phase advance idempotent.
