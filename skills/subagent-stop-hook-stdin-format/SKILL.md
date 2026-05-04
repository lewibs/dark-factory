---
name: subagent-stop-hook-stdin-format
description: "SubagentStop hook scripts receive the matched agent name as plain text on stdin (first line), not as JSON — unlike PreToolUse/PostToolUse hooks which receive JSON."
user-invocable: false
---
## When to use

When writing a bash script that is wired as a `SubagentStop` hook for an agent. Use this to correctly read which agent fired the hook and to avoid confusing the plain-text stdin format with the JSON format used by other hook types.

## Steps

1. Read the agent name from the first line of stdin:
   ```bash
   agent_type=$(head -n1)
   ```
   Do NOT attempt to parse it as JSON. The input is just the raw agent name string (e.g., `skeleton-agent`).

2. Branch on the agent name with a `case` statement:
   ```bash
   case "$agent_type" in
     skeleton-agent)
       # handle skeleton-agent stop
       ;;
     testing-agent)
       # handle testing-agent stop
       ;;
     *)
       echo "agent_type not recognized: $agent_type" >&2
       exit 0
       ;;
   esac
   ```

3. Always exit 0 from SubagentStop hooks — even on errors — so that hook failure never blocks the agent pipeline. Log errors to stderr instead:
   ```bash
   git -C "$work_dir" commit -m "$commit_msg" 2>/dev/null || {
     echo "git commit failed" >&2
     exit 0
   }
   ```

4. Declare the hook in the agent's YAML frontmatter (NOT in `hooks/hooks.json`). Add a `SubagentStop:` key to the frontmatter of the agent `.md` file:
   ```yaml
   ---
   name: skeleton-agent
   description: "..."
   tools: Read, Write, Edit, Bash
   SubagentStop: "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/your-hook.sh"
   ---
   ```
   This keeps the hook co-located with the agent's instructions. Each agent that needs a SubagentStop hook declares it directly in its own frontmatter rather than via a central regex matcher in `hooks/hooks.json`. See the `subagent-stop-in-agent-frontmatter` skill for full details on this pattern.

## Notes

- The plain-text stdin format contrasts with `PreToolUse` and `PostToolUse` hooks, which receive the full tool call input as JSON on stdin. Do not call `jq` or `json.loads()` on SubagentStop stdin.
- SubagentStop hooks are no longer declared in `hooks/hooks.json` with a regex matcher. They are declared per-agent in YAML frontmatter. This means each hook script is no longer responsible for branching on multiple agent names — one script per agent (or shared scripts that don't need to branch) is the expected shape.
- In tests, pass the agent name as a plain string (not JSON-encoded) to the subprocess `input=` parameter. See the `test-bash-hook-scripts-with-pytest` skill for the test harness pattern.
- `DARK_FACTORY_WORK_DIR` is still available as an environment variable in SubagentStop hooks, just as in other hook types.
