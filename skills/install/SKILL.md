---
name: install
description: Install or update the dark-factory plugin in Claude Code.
user-invocable: true
---

## Install (one-time)

```bash
# 1. Register the local repo as a marketplace
claude plugin marketplace add /home/lewibs/github/dark_factory/dark_factory

# 2. Install the plugin
claude plugin install dark-factory
```

## Update (after pulling new changes)

```bash
git -C /home/lewibs/github/dark_factory/dark_factory pull
claude plugin update dark-factory
```

## Verify

```bash
claude plugin list
```

## Available commands after install

| Command | Description |
|---|---|
| `/dark-factory:dark-factory` | Full orchestration — feature, debug, or fix-flow end-to-end |
| `/dark-factory:init` | Initialize a new project with dark factory |
