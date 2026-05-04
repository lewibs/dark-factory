---
name: subagent-stop-in-agent-frontmatter
description: "SubagentStop hooks for dark-factory agents are declared in the YAML frontmatter of the agent's .md file, not in hooks/hooks.json — each agent carries its own stop-hook declaration."
user-invocable: false
---
## When to use

Whenever you need to wire a SubagentStop hook to a dark-factory agent (any file under `agents/**/*.md`). Also use this when you see a SubagentStop entry in `hooks/hooks.json` — that is the old pattern and should be migrated.

## Steps

1. Open the target agent's `.md` file (e.g., `agents/featurework/execution/agents/skeleton-agent.md`).

2. In the YAML frontmatter block (between the `---` delimiters), add a `SubagentStop:` key whose value is the shell command to run:
   ```yaml
   ---
   name: skeleton-agent
   description: "..."
   tools: Read, Write, Edit, Bash
   SubagentStop: "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/commit-on-subagent-stop.sh"
   ---
   ```
   Use `${CLAUDE_PLUGIN_ROOT}` as the prefix for all plugin script paths so the hook resolves correctly from any install location.

3. If multiple agents need the same hook script, add the identical `SubagentStop:` line to each agent's frontmatter independently. Do NOT add a single shared entry to `hooks/hooks.json`.

4. If two agents need different hook scripts, each gets its own `SubagentStop:` line pointing to its own script.

5. Do NOT add a `SubagentStop` entry to `hooks/hooks.json`. That file is for `PreToolUse`, `PostToolUse`, and `Stop` global hooks only.

6. After editing, reinstall the plugin with `/dark-factory:install` to pick up the frontmatter changes.

## Notes

- The `SubagentStop:` YAML field is read directly by Claude Code from the agent frontmatter. It is not a custom dark-factory extension — it is a first-class Claude Code feature for per-agent stop hooks.
- Keeping the hook declaration in the agent's own file means the hook is visible alongside the agent's instructions, tools, and skills, rather than being hidden in a central hooks.json with a regex matcher.
- The hook script still receives the agent name as plain text on stdin (not JSON). See the `subagent-stop-hook-stdin-format` skill for how to read it. However, since each agent now has its own dedicated hook, branching on agent name inside the script is no longer necessary for the common case.
- The existing scripts (`commit-on-subagent-stop.sh` and `pr-agent-cleanup-hook.sh`) were not changed during this migration — only where the hook is declared changed.
- `${CLAUDE_PLUGIN_ROOT}` is available in the hook execution environment when the plugin is properly installed. Do not hardcode absolute paths.
