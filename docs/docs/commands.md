# Commands

## Overview

The `commands/` directory contains the three Claude Code slash commands that Dark Factory exposes to the developer. Each command file is a minimal markdown stub that delegates all logic to the corresponding orchestrator agent.

## Command Files

### manufacture

**File:** `commands/manufacture.md`

```
/dark-factory:manufacture <task description>
```

Delegates to `agents/dark-factory/agents/dark-factory-agent.md`.

Full end-to-end orchestration: classifies the task, routes to the appropriate worker (feature, debugger, or fix-flow), runs code review and documentation update, opens and merges a PR, and cleans up. Accepts a free-text task description as input (e.g. "add OAuth login", "fix the login crash", "pipeline is failing").

---

### init

**File:** `commands/init.md`

```
/dark-factory:init [github_url]
```

Delegates to `agents/initialization/agents/init-orchestrator-agent.md`.

Onboards a project onto Dark Factory. Optionally accepts a GitHub URL; if omitted, treats the current working directory as the project to initialize. Sets up `docs/docs/`, `docs/plans/`, `docs/bugs/` directories, generates `CLAUDE.md`, and opens an "init: dark factory" PR.

---

### update

**File:** `commands/update.md`

```
/dark-factory:update
```

Updates the Dark Factory plugin to the latest version via `git pull` and `claude plugin update dark-factory`. Takes no arguments.

## Relationship to Agents

Commands are thin wrappers. Their front-matter carries a `description` for display in Claude Code's command picker, and their body contains a single line: `Follow the instructions in <agent-path> exactly.`

All orchestration logic lives in `agents/`, not in `commands/`.
