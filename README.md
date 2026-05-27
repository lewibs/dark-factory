```
██████╗  █████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝
██║  ██║███████║██████╔╝█████╔╝
██║  ██║██╔══██║██╔══██╗██╔═██╗
██████╔╝██║  ██║██║  ██║██║  ██╗
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
███████╗ █████╗  ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
█████╗  ███████║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝
██╔══╝  ██╔══██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝
██║     ██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║
╚═╝     ╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝
```

Dark Factory is a fully autonomous coding plugin for Claude Code. Focused commands. No hand-holding. Done.

| | |
|---|---|
| **Build features** | Plans, implements, reviews, and ships new functionality end-to-end |
| **Fix bugs** | Diagnoses failures, applies fixes, and verifies — without you touching the code |
| **Repair broken flows** | Applies targeted changes, loops through test failures, and restores green CI |
| **Investigate systems** | Documents any system from source, validates every claim against the code |

For a deeper look at how it works, see the [system documentation](https://github.com/lewibs/dark-factory/blob/main/docs/docs/README.md).

## Install

```sh
claude plugin marketplace add https://github.com/lewibs/dark-factory
claude plugin install dark-factory
```

## Update

```sh
claude plugin marketplace update dark-factory
claude plugin uninstall dark-factory
claude plugin install dark-factory
```

## Verify

```sh
claude plugin list
```

## How does it work?

Each command is a focused orchestrator that delegates to a single dedicated worker agent. You describe the task; the agent handles planning, implementation, code review, PR, and cleanup.

Feature work uses a structured plan template before a single line of code is written:

- **[Plan template](https://github.com/lewibs/dark-factory/blob/main/agents/featurework/planning/templates/plan-template.md)** — captures system intent, a Mermaid architecture diagram, and an explicit flow checklist. The planner walks you through each section for approval before handing off to the implementation agent.
- **[Bug template](https://github.com/lewibs/dark-factory/blob/main/skills/debug/templates/bug-audit-log-template.md)** — before touching any code, the debugger fills out a structured audit log: reproduction steps, system boundary, root cause, and fix hypothesis. No guessing, no thrashing.

## Commands

| Command | Input | Description |
|---|---|---|
| `/dark-factory:plan` | Task description | Plans a feature end-to-end — walks through system intent, architecture diagram, and per-flow approval gates, then opens a PR with the approved plan |
| `/dark-factory:execute` | Path to an approved plan file | Implements an approved plan — runs the full execution pipeline, code review, and opens a PR |
| `/dark-factory:debug` | Bug description | Diagnoses and fixes a non-obvious bug — fills out a bug audit log, applies the fix, runs code review, and opens a PR |
| `/dark-factory:repair` | Change description | Applies a small targeted change — no plan required, runs tests in a loop until green, opens a PR |
| `/dark-factory:investigation` | System name or topic | Investigates a system and writes authoritative documentation to `docs/docs/` |
| `/dark-factory:gotoworktree` | PR number, task name, or description | Finds or creates the matching git worktree and pulls main/master — use this before running any other command |
| `/dark-factory:build-factory` | Optional terminal name | Opens a new gnome-terminal running `claude /remote-control` for parallel factory sessions |
| `/dark-factory:install` | None | Install or reinstall the plugin (run from repo root after `git pull`) |
| `/dark-factory:reset` | None | Switch back to the main branch in the main worktree and pull the latest code |
