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

The command invokes the Python script at `scripts/gen_hooks.py` with the current project directory, which performs the following:

1. **scanFrontmatter**: Recursively scans all `.md` files in the project for YAML frontmatter containing hook declarations (PreToolUse, PostToolUse, Stop, SubagentStop, PreCompact)
2. **mergeIntoSettings**: Merges discovered hooks into `.claude/settings.json` additively, preserving existing entries and deduplicating by command string
3. **genHooksCommand**: Orchestrates both flows and returns a summary message

### Output

Returns a message indicating the number of hooks added and duplicates skipped, along with the path to `.claude/settings.json`.
