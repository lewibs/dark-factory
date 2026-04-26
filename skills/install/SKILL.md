---
name: install
description: Install or update the dark-factory plugin in Claude Code.
user-invocable: true
---

## Install (one-time)

From anywhere inside the cloned repo:

```bash
bash agents/initialization/scripts/install-plugin.sh
```

This script auto-detects the repo location — works for any user on any machine.

## Update (after pulling new changes)

```bash
git pull
claude plugin update dark-factory
```

## Verify

```bash
claude plugin list
```

## Available commands after install

| Command | Description |
|---|---|
| `/dark-factory:manufacture` | Full orchestration — feature, debug, or fix-flow end-to-end |
| `/dark-factory:init` | Initialize a new project with dark factory |
| `/dark-factory:update` | Update the plugin to the latest version |
