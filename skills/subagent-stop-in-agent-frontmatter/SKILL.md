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
- `${CLAUDE_PLUGIN_ROOT}` is available in the hook execution environment when the plugin is properly installed. Do not hardcode absolute paths.
- **`commit-on-subagent-stop.sh` is the general-purpose commit hook for file-generating agents.** It uses a `case` statement keyed on agent name to select the commit message. The current recognized agents are: `skeleton-agent`, `testing-agent`, `implementation-agent`, `sub-planning-agent`, `detect-drift-agent`, `update-documentation-agent`, `skill-update-agent`, `setup-wizard`, `debugger-agent`, `repair-agent`. The `*)` catch-all prints a warning to stderr and exits 0 (no commit). When adding a new file-generating agent to this script, add a new `case` branch with a descriptive commit message.
- **`commit-investigation-docs.sh` handles investigation-style agents** (`investigation-orchestrator`, `investigation-agent`). It follows the same `case` pattern. If your new agent writes documentation or investigation artifacts, prefer extending this script or creating a new dedicated script rather than mixing concerns into `commit-on-subagent-stop.sh`.
- When a new agent's name is not listed in any script's `case` statement, the script silently exits 0 — the commit never runs and no error is surfaced to the user. Always verify the agent name is present in the relevant script after wiring a new `SubagentStop` frontmatter entry.
- After extending a hook script, run `/dark-factory:gen-hooks` and verify the agent entry appears in `.claude/settings.json` with the correct path.
- **CRITICAL: Never add `SubagentStop` entries to `.claude/settings.json`.** Global SubagentStop hooks in `settings.json` fire for ALL subagents with no way to scope them to a specific agent. If a worktree-destroying hook (e.g., `pr-agent-cleanup-hook.sh`) is registered globally, it will fire when any agent finishes — including `repair-agent` and `debugger-agent` — and will destroy the feature worktree before the orchestrating agent (dark-factory-agent) completes its remaining steps. This causes a subtle stuck/never-completes symptom with no obvious error. The `hooks` key in `settings.json` should contain only `PreToolUse`, `PostToolUse`, and `Stop` entries, never `SubagentStop`. If you find `SubagentStop` entries in `settings.json`, remove them — the per-agent frontmatter declarations are already sufficient and correct. The regression test `tests/test_manufacture_flow_violations.py::TestSubagentStopNotInSettingsJson` enforces this invariant.
