---
name: declare-hooks-in-md-frontmatter
description: "Users can declare Claude Code hooks (PreToolUse, PostToolUse, Stop, SubagentStop, PreCompact) in YAML frontmatter of any .md file; running /dark-factory:gen-hooks activates them in .claude/settings.json."
user-invocable: false
---
## When to use

Any time you need to attach a shell script to a Claude Code hook event (PreToolUse, PostToolUse, Stop, SubagentStop, PreCompact) and want the declaration to live alongside the skill, agent, or command file that owns it — rather than editing `.claude/settings.json` directly.

Also use this skill when explaining to users how to register their own hook scripts without touching plugin internals.

## Steps

1. In the YAML frontmatter of any `.md` file (skill, agent, command, or any project markdown), add a key matching one of the supported hook event names with the script path as the value:

   ```yaml
   ---
   name: my-skill
   PreToolUse: ./hooks/pre-use.sh
   PostToolUse: ./hooks/post-use.sh
   ---
   ```

2. Multiple hooks of the same type are supported — declare them as a YAML list:

   ```yaml
   ---
   name: my-skill
   PreToolUse:
     - ./hooks/first.sh
     - ./hooks/second.sh
   ---
   ```

   Note: YAML does not support duplicate keys in a single mapping. Use a list for multiple values under the same event type.

3. Run `/dark-factory:gen-hooks` from the project root. The command scans all `.md` files recursively and merges any discovered hook declarations into `.claude/settings.json` under the `hooks` key.

4. Verify by inspecting `.claude/settings.json` — each declared hook appears as:
   ```json
   {
     "matcher": "",
     "hooks": [{ "type": "command", "command": "bash ./hooks/pre-use.sh" }]
   }
   ```
   The `matcher` defaults to `""` (matches all tools/events).

## Notes

- The `gen-hooks` command is additive: it never deletes existing hooks in `settings.json`. Re-running it after adding new declarations is safe.
- Deduplication is by exact command string (`bash <path>`). Running `gen-hooks` twice does not add duplicate entries.
- This mechanism writes to the user-local `.claude/settings.json` (project-level settings). It is distinct from the plugin-level `hooks/hooks.json` mechanism (see `skills/register-plugin-hooks-in-hooks-json/SKILL.md`), which ships hooks with the installed plugin.
- The supported hook event names are exactly: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `PreCompact`. Any other frontmatter key is ignored by `gen-hooks`.
- The backing implementation is `scripts/gen_hooks.py`. The slash command is `commands/gen-hooks.md`.
