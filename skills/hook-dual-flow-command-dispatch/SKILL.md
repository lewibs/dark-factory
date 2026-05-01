---
name: hook-dual-flow-command-dispatch
description: "How to implement a single hook script that serves two distinct flows (e.g., check and mutate) by dispatching on a 'command' field in tool_input, so both guard and write operations share one registration."
user-invocable: false
---
## When to use

When a hook needs to handle two logically related but distinct operations — for example, a pre-tool-use guard that checks state and a separate write path that marks state as complete — and you want to register only one hook entry rather than two separate scripts.

The pattern uses `tool_input.command` as a discriminator field. Callers that want the mutate path set `command` explicitly; calls without `command` default to the check path.

## Steps

1. In the hook's `main()`, read the `command` field from `tool_input`:
   ```bash
   command_field=$(printf '%s' "$tool_input" | jq -r '.tool_input.command // ""')
   ```

2. Dispatch to the appropriate function based on the field value:
   ```bash
   if [ "$command_field" = "mark-phase-complete" ]; then
     agent_name=$(printf '%s' "$tool_input" | jq -r '.tool_input.agentName // ""')
     phase_number=$(printf '%s' "$tool_input" | jq -r '.tool_input.phaseNumber // 0')
     markPhaseComplete "$agent_name" "$phase_number"
     return
   fi

   # Default: check path
   agent_name=$(printf '%s' "$tool_input" | jq -r '.tool_input.agentName // ""')
   current_phase=$(printf '%s' "$tool_input" | jq -r '.tool_input.currentPhase // 0')
   checkPhaseOrder "$agent_name" "$current_phase"
   ```

3. Implement both functions in the same script. Each function outputs JSON to stdout and calls `exit 0` (never a non-zero exit — hooks must not crash Claude Code). The mutate function calls `markPhaseComplete`; the guard function calls `checkPhaseOrder` or equivalent.

4. Register the hook once in `hooks/hooks.json`:
   ```json
   {
     "PreToolUse": [
       {
         "matcher": "",
         "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/my-hook.sh\"" }]
       }
     ]
   }
   ```
   Both flows use the same registration. The `command` field in `tool_input` selects which code path runs at call time.

5. In tests, exercise each path by setting or omitting the `command` field in the test fixture:
   ```python
   # Check path (no command field)
   hook_input = {"tool_name": "Agent", "tool_input": {"agentName": "dark-factory-agent", "currentPhase": 2}}

   # Mutate path
   hook_input = {"tool_name": "Bash", "tool_input": {"command": "mark-phase-complete", "agentName": "dark-factory-agent", "phaseNumber": 1}}
   ```

## Notes

- Use a string enum for `command` values (e.g., `"mark-phase-complete"`) rather than a boolean flag so the dispatch is extensible to more than two paths in the future.
- The `command` field is read from `tool_input.command` (one level inside the outer `tool_input` object), not from the top-level hook JSON. The outer `tool_name` field identifies the Claude tool type (e.g., `Agent`, `Bash`) and is separate.
- Missing or empty `command` always falls through to the default (check) path. This keeps ordinary Agent/tool invocations on the safe read-only path with no additional fields required.
- Both functions must be idempotent or at least safe to call multiple times, because hooks fire for every matching tool invocation — including retries.
- Do not branch on `tool_name` to distinguish the two paths. `tool_name` reflects the Claude tool being used (e.g., `Bash`, `Agent`), not the intent. The `command` field inside `tool_input` is the correct discriminator for intent.
