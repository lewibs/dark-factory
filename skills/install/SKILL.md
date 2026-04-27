---
name: install
description: Install or update the dark-factory plugin in Claude Code.
user-invocable: true
---

## Install (one-time)

```bash
git clone https://github.com/lewibs/dark-factory
cd dark-factory
claude plugin marketplace add "$(pwd)"
claude plugin install dark-factory
bash scripts/reopen-remote-control.sh "dark factory"
```

## Update

```bash
git pull
claude plugin marketplace add "$(pwd)"
claude plugin marketplace update dark-factory
claude plugin uninstall dark-factory
claude plugin install dark-factory
bash scripts/reopen-remote-control.sh "dark factory"
```

## Verify

```bash
claude plugin list
```

## Launcher script

`scripts/reopen-remote-control.sh` opens a new terminal in your current directory running Claude in remote-control mode, then closes the current terminal.

```bash
# Usage: pass a name for the remote-control session
bash scripts/reopen-remote-control.sh "my project"
```

## Commands available after install

| Command | Description |
|---|---|
| `/dark-factory:manufacture` | Full orchestration — feature, debug, or fix-flow end-to-end |
| `/dark-factory:init` | Initialize a new project with dark factory |
| `/dark-factory:update` | Update the plugin to the latest version |
