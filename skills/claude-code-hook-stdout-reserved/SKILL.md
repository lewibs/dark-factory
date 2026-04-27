---
name: claude-code-hook-stdout-reserved
description: "In Claude Code PreToolUse hooks, stdout is the override channel for the tool input JSON — all diagnostic logging must go to stderr, never stdout."
user-invocable: false
---
## When to use

Whenever writing or modifying a Claude Code `PreToolUse` hook script (e.g., in `.claude/settings.json` under `"PreToolUse"`).

## Steps

1. Read the tool call input from stdin:
   ```bash
   TOOL_INPUT=$(cat)
   ```

2. Do all your work on the data. If you want to log anything, send it to stderr:
   ```bash
   echo "my-hook | some-path | key=value" >&2
   ```

3. When exiting early (pass-through, error, or no-brain case), you must still emit the unmodified tool input on stdout so Claude Code can continue:
   ```bash
   cat   # re-emit stdin unchanged
   exit 0
   ```
   Or if you already consumed stdin with `$(cat)`:
   ```bash
   printf '%s' "$TOOL_INPUT"
   exit 0
   ```

4. Emit the (possibly modified) tool input JSON on stdout as the final action.
   For hooks that handle both Agent tool calls (prompt nested under `.tool_input`)
   and non-Agent tool calls (prompt at top level), use the conditional form:
   ```bash
   printf '%s' "$TOOL_INPUT" | jq --arg p "$NEW_PROMPT" \
     'if .tool_input.prompt != null then .tool_input.prompt = $p else .prompt = $p end'
   ```
   See the `agent-tool-json-nesting` skill for details on the Agent tool's JSON shape.

## Notes

- Claude Code reads the hook's stdout to determine the final tool input. Any stray text on stdout will corrupt the JSON and cause the tool call to fail.
- `PostToolUse` hooks do not have this constraint — they do not modify tool input, so stdout is safe to use for logging. The stdout-reserved rule applies only to `PreToolUse` hooks that need to override the tool input.
- In the early-exit (no-brain) path, you must still output the original tool input on stdout. Exiting with code 0 and no stdout causes Claude Code to see an empty tool input.
- Do NOT use `.prompt = $p` directly on an Agent tool call — the prompt is nested under `.tool_input.prompt`, so the top-level write is silently ignored.
