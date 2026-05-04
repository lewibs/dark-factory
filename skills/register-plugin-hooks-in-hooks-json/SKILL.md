---
name: register-plugin-hooks-in-hooks-json
description: "Plugin-level Claude Code hooks must be declared in hooks/hooks.json (referenced from plugin.json), not in .claude/settings.json, so they ship and resolve correctly with the installed plugin."
user-invocable: false
---
## When to use

Any time you add, remove, or modify a Claude Code PreToolUse, PostToolUse, or Stop hook that belongs to the dark-factory plugin — as opposed to a project-local hook that a user configures themselves.

**SubagentStop hooks are NOT declared in hooks.json.** They are declared in the YAML frontmatter of the individual agent `.md` file. See the `subagent-stop-in-agent-frontmatter` skill for how to declare them.

## Steps

1. Open `hooks/hooks.json` in the plugin root (create it if it does not exist). It must follow this structure:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         { "matcher": "Agent", "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/pre-tool-use-hook.sh\"" }] }
       ],
       "PostToolUse": [
         { "matcher": "Agent", "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/post-tool-use-hook.sh\"" }] }
       ]
     }
   }
   ```
2. Ensure `plugin.json` declares the hooks file:
   ```json
   {
     "hooks": "./hooks/hooks.json"
   }
   ```
3. Do NOT add plugin hooks to `.claude/settings.json`. That file is for project-level or user-level overrides. Plugin hooks in `settings.json` are not portable — they use relative paths that break when the plugin is installed outside the repo.
4. Use `${CLAUDE_PLUGIN_ROOT}/` prefix for all script paths inside hook commands (see the `plugin-root-script-paths` skill at `skills/plugin-root-script-paths/SKILL.md`).

## Notes

- `.claude/settings.json` hooks use bare relative paths (e.g. `bash agents/dark-factory/scripts/foo.sh`) which only work when the CWD matches the plugin repo root. `hooks/hooks.json` hook commands using `${CLAUDE_PLUGIN_ROOT}` resolve correctly regardless of CWD.
- If you need a hook for a one-project use case (not part of the plugin), use `.claude/settings.json` as normal — this rule applies only to hooks that are part of the plugin itself.
- After modifying `hooks/hooks.json`, reinstall the plugin with `/dark-factory:install` to pick up the changes.
- `SubagentStop` hooks are NOT in `hooks/hooks.json`. They live in the YAML frontmatter of the individual agent `.md` file as a `SubagentStop:` key. This keeps each agent's stop-hook co-located with its instructions rather than relying on a central regex matcher. See the `subagent-stop-in-agent-frontmatter` skill for the correct approach.
