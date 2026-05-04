---
description: "Scan all agent, skill, and command files for hook declarations in YAML frontmatter and sync them to hooks/hooks.json without duplicates"
---

Run the gen_hooks.py script to scan all .md files under agents/, skills/, and commands/ directories for hook declarations, then merge them into hooks/hooks.json.

Hook declarations go in the YAML frontmatter of a .md file:

```yaml
---
name: my-agent
hooks:
  - event: PreToolUse
    matcher: "Agent"
    script: agents/featurework/scripts/my-hook.sh
  - event: PostToolUse
    matcher: "Bash"
    script: agents/featurework/scripts/my-post-hook.sh
---
```

To use this command:

1. Add `hooks:` declarations to any agent (.md in agents/), skill (SKILL.md in skills/), or command (.md in commands/) file
2. Run `/gen-hooks` to sync the hooks to hooks/hooks.json
3. The script is idempotent — running it multiple times will not create duplicates

Valid hook events: `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop`

The script will:
- Scan all .md files recursively in agents/, skills/, and commands/
- Parse YAML frontmatter from each file
- Check if each hook already exists in hooks/hooks.json
- Add new hooks and skip duplicates
- Print a summary of hooks added and skipped

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gen_hooks.py"
```
