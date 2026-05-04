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
Made by Benjamin Lewis CEO - [github](https://github.com/lewibs/dark-factory/tree/main)

Dark Factory is a fully autonomous coding plugin for Claude Code. One command. No hand-holding. Done.

| | |
|---|---|
| **Build features** | Designs, implements, reviews, and ships new functionality end-to-end |
| **Fix bugs** | Diagnoses failures, applies fixes, and verifies — without you touching the code |
| **Repair broken flows** | Detects broken integrations, loops through fixes, and restores green CI |

All three run 100% autonomously — Dark Factory handles planning, implementation, code review, PR, and cleanup from start to finish.

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

Dark Factory requires your input exactly twice: once to describe the task, and once to approve the result. Everything in between is autonomous.

Execution is enforced by two complementary primitives:

- **[Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)** — PreToolUse/PostToolUse scripts fire around every tool call, injecting shared state, enforcing phase order, and blocking agents from drifting outside their lane. Determinism isn't hoped for — it's mechanically enforced.
- **Structured templates** — every task is grounded in one of two blueprints before a single line of code is written:
  - **[Plan template](https://github.com/lewibs/dark-factory/blob/main/agents/featurework/planning/templates/plan-template.md)** — drives feature work. The plan captures system intent, a Mermaid architecture diagram, and an explicit flow checklist. Agents cannot advance past a phase until the previous one is checked off.
  - **[Bug template](https://github.com/lewibs/dark-factory/blob/main/skills/debug/templates/bug-audit-log-template.md)** — drives debugging. Before touching any code, agents fill out a structured audit log: reproduction steps, system boundary, root cause, and fix hypothesis. No guessing, no thrashing.

These two templates are the source of truth that every downstream agent — planner, implementer, reviewer, PR opener — reads from. They keep the factory on rails from the first commit to the final green CI check.

## Commands

| Command | Input | Description |
|---|---|---|
| `/dark-factory:manufacture` | Task description (e.g. "add OAuth login") | Full orchestration — routes to the right agent (feature, debug, or fix-flow) end-to-end, runs code review, opens a PR, and cleans up |
| `/dark-factory:build-factory` | Optional terminal name | Opens a new gnome-terminal running `claude /remote-control` for parallel factory sessions |
| `/dark-factory:install` | None | Install or reinstall the plugin (run from repo root after `git pull`) |
