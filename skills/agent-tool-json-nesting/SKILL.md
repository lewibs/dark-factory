---
name: agent-tool-json-nesting
description: "When a Claude Code PreToolUse hook intercepts an Agent tool call, the prompt and subagent_type live under .tool_input, not at the top level of the hook stdin JSON."
user-invocable: false
---
## When to use

Whenever writing or modifying `pre-tool-use-hook.sh` logic that reads or writes
fields from an `Agent` tool call (e.g., to inject text into the prompt, read
`subagent_type`, or modify any other Agent parameter).

## Steps

1. The raw hook stdin for an Agent tool call looks like this:
   ```json
   {
     "tool_name": "Agent",
     "tool_input": {
       "subagent_type": "testing-agent",
       "prompt": "original prompt text"
     }
   }
   ```
   Note the extra nesting level: fields are under `.tool_input`, not at the
   root of the JSON object.

2. Read `subagent_type` with:
   ```bash
   AGENT_NAME=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.subagent_type // ""')
   ```

3. Read the prompt with:
   ```bash
   ORIGINAL_PROMPT=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.prompt // ""')
   ```

4. Write a modified prompt back with:
   ```bash
   TOOL_INPUT=$(printf '%s' "$TOOL_INPUT" | jq --arg p "$NEW_PROMPT" '.tool_input.prompt = $p')
   ```

5. When emitting the final output, handle both Agent tool calls (nested) and
   non-Agent tool calls (top-level prompt) defensively:
   ```bash
   printf '%s' "$TOOL_INPUT" | jq --arg p "$NEW_PROMPT" \
     'if .tool_input.prompt != null then .tool_input.prompt = $p else .prompt = $p end'
   ```

## Notes

- Non-Agent tool calls (e.g., Bash, Read) do NOT have a `.tool_input.prompt`
  field. Using `.tool_input.prompt // .prompt` as a read path and the
  conditional `if .tool_input.prompt != null` as a write path keeps the hook
  safe for both shapes.
- The bug this prevents: using `.prompt = $p` directly on an Agent tool call
  sets a new top-level `.prompt` field while leaving `.tool_input.prompt`
  unchanged — the injected text is silently ignored by Claude Code.
- Always guard Agent-specific logic behind `if [ "$TOOL_NAME" = "Agent" ]` to
  avoid accidentally reading `.tool_input.subagent_type` from other tools that
  happen to have a `tool_input` wrapper.
