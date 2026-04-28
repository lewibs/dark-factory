---
name: invoke-claude-from-hook
description: "How to spawn a `claude` subprocess from inside a PostToolUse hook script without triggering recursive hook re-entrancy."
user-invocable: false
---
## When to use

When a PostToolUse (or PreToolUse) hook needs to call a Claude agent directly — e.g., running a documentation agent in the background after the worker phase completes — rather than having the orchestrator invoke it via the `Agent` tool.

## Steps

1. Detect the triggering condition using brain.json state, e.g.:
   ```bash
   if [ "${RUNNING_PHASE:-}" = "worker-running" ]; then
   ```

2. Read the agent's prompt file and any context from brain.json:
   ```bash
   AGENT_PATH="${WORK_DIR}/agents/some/agents/some-agent.md"
   AGENT_INSTRUCTIONS=$(cat "$AGENT_PATH")
   EXTRA_CONTEXT=$(jq -r '.someField // ""' "$BRAIN_PATH")
   PROMPT="${AGENT_INSTRUCTIONS}

   ${EXTRA_CONTEXT}"
   ```

3. **Critical: `unset DARK_FACTORY_WORK_DIR` inside the subshell** before calling `claude`. If this variable is set, Claude Code will fire the same PostToolUse hook recursively for every tool call the subprocess makes, causing infinite re-entrancy.

4. Run `claude` synchronously from a subshell, `cd`-ing into WORK_DIR first:
   ```bash
   LOG_FILE="/tmp/some-agent-$$.log"
   (
     cd "$WORK_DIR"
     unset DARK_FACTORY_WORK_DIR
     claude --model claude-sonnet-4-6 \
            --allowedTools "Read,Grep,Glob,Write,Edit,Bash" \
            -p "$PROMPT" >"$LOG_FILE" 2>&1
   )
   EXIT_CODE=$?
   echo "hook | invoke-claude | exit=${EXIT_CODE} log=${LOG_FILE}" >&2
   ```

5. Update brain.json phase flags around the invocation (mark running before, complete after) so the phase sequencer tracks it correctly:
   ```bash
   # Before launching
   DOCS_TMP=$(mktemp /tmp/brain-XXXXXX.json)
   _TMP_FILES+=("$DOCS_TMP")
   jq '.phases["docs-running"] = true' "$BRAIN_PATH" > "$DOCS_TMP" \
     && mv "$DOCS_TMP" "$BRAIN_PATH"

   # ... call claude ...

   # After (mark complete even on non-zero exit if the step is non-fatal)
   DOCS_TMP2=$(mktemp /tmp/brain-XXXXXX.json)
   _TMP_FILES+=("$DOCS_TMP2")
   jq '.phases["docs-running"] = false | .phases["docs-complete"] = true' "$BRAIN_PATH" \
     > "$DOCS_TMP2" && mv "$DOCS_TMP2" "$BRAIN_PATH"
   ```

6. The phase flags for this hook-driven step must still be declared in the orchestrator's initial brain.json `phases` object and must appear in the correct sequence position so the pre-hook's phase sequencer does not misinterpret them. For example, if the step runs after `worker-complete` and before `review-running`, declare:
   ```json
   "worker-complete": true,
   "docs-running": false,
   "docs-complete": false,
   "review-running": false,
   ```

## Notes

- The `unset DARK_FACTORY_WORK_DIR` inside the subshell is the sole guard against recursive hook re-entrancy. Without it, every `Agent` or `Bash` tool call the subprocess makes will re-trigger this hook.
- Use `--allowedTools` to restrict the subprocess to only the tools it actually needs. Overly permissive tool lists can cause the docs agent to invoke `Agent`, which would still be matched by the hook even with the env var unset (because it is a new top-level Claude session with its own hooks).
- Keep the invocation synchronous if the result must land in the worktree before the next step (e.g., before the pr-agent does `git add --all`). Use background `&` only if the result is truly fire-and-forget.
- Temp files created with `mktemp` inside the hook should be tracked in `_TMP_FILES` and cleaned up with a `trap _cleanup_tmp EXIT` pattern to avoid leaking files on `/tmp`.
- Log output to a stable path like `/tmp/<agent>-$$.log` (using `$$` for the hook's PID) so each run gets a unique log file and you can inspect failures.
