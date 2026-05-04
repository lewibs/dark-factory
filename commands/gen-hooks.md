---
name: gen-hooks
description: Scans YAML frontmatter of skill/agent/command files for hook declarations and writes them to .claude/settings.json additively
---

# gen-hooks

## Purpose

Scans all `.md` files in the project directory for YAML frontmatter hook declarations (e.g., `PreToolUse: ./hooks/pre-use.sh`) and merges them into `.claude/settings.json` without disturbing existing entries.

## Usage

```
/dark-factory:gen-hooks
```

## Implementation

TODO: genHooksCommand flow implementation
