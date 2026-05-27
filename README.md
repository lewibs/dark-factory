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
| [/dark-factory:plan](docs/docs/plan-command-agent.md) | Task description | Plans a feature end-to-end — walks through system intent, architecture diagram, and per-flow approval gates, then saves the approved plan |
| [/dark-factory:execute](docs/docs/execute-command-agent.md) | Path to an approved plan file | Implements an approved plan — runs the full execution pipeline, code review, and opens a PR |
| [/dark-factory:debug](docs/docs/debug-command-agent.md) | Bug description | Diagnoses and fixes a non-obvious bug — fills out a bug audit log, applies the fix, runs code review, and opens a PR |
| [/dark-factory:repair](docs/docs/repair-command-agent.md) | Change description | Applies a small targeted change — no plan required, runs tests in a loop until green, opens a PR |
| [/dark-factory:investigation](docs/docs/investigation-command.md) | System name or topic | Investigates a system and writes authoritative documentation to `docs/docs/` |
| [/dark-factory:save](docs/docs/save-command.md) | Optional task description | Commits current changes and opens or updates a PR — lightweight shortcut that skips code review and docs pipeline |
| [/dark-factory:goto](docs/docs/gotoworktree-command-agent.md) | PR number, task name, or description | Finds or creates the matching git worktree and pulls main/master — use this before running any other command |
| [/dark-factory:build-factory](docs/docs/build-factory.md) | Optional terminal name | Opens a new gnome-terminal running `claude /remote-control` for parallel factory sessions |
| [/dark-factory:destroy-factory](docs/docs/destroy-factory.md) | Optional terminal name | Terminates all other running Claude/dark-factory terminal sessions and spawns one fresh factory terminal |
| [/dark-factory:gen-hooks](docs/docs/gen-hooks.md) | None | Scans YAML frontmatter of skill/agent/command files for hook declarations and writes them to `.claude/settings.json` |
| [/dark-factory:install](docs/docs/install.md) | None | Install or reinstall the plugin (run from repo root after `git pull`) |
