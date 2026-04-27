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

## Commands

| Command | Input | Description |
|---|---|---|
| `/dark-factory:manufacture` | Task description (e.g. "add OAuth login") | Full orchestration — routes to the right agent (feature, debug, or fix-flow) end-to-end, runs code review, opens a PR, and cleans up |
| `/dark-factory:init` | Optional GitHub URL | Onboard a project onto dark factory — sets up the structure for infinite autonomous changes and generates a CLAUDE.md |
| `/dark-factory:install` | None | Install or reinstall the plugin (run from repo root after `git pull`) |
