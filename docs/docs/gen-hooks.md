# /dark-factory:gen-hooks

Scans YAML frontmatter of skill/agent/command files for hook declarations and writes them to `.claude/settings.json` additively.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:gen-hooks"] --> Cmd["commands/gen-hooks.md"]
  Cmd -->|"python scripts/gen_hooks.py"| Scan["Scan all .md files<br/>for YAML frontmatter"]
  Scan --> Extract["Extract hook declarations<br/>(PreToolUse, PostToolUse, etc)"]
  Extract --> Merge["Merge into .claude/settings.json<br/>additively"]
  Merge --> Done["Done: hooks registered"]
```

## See also

- scripts/gen_hooks.py — hook discovery and settings.json update
- [hooks documentation](hooks.md) — hook types and usage
