---
name: install
description: Install or update the dark-factory plugin in Claude Code.
user-invocable: true
---

## Install (one-time, run from inside the cloned repo)

```bash
claude plugin marketplace add .
claude plugin install dark-factory
```

## Update

```bash
git pull
claude plugin update dark-factory
```

## Verify

```bash
claude plugin list
```

## Commands available after install

| Command | Description |
|---|---|
| `/dark-factory:manufacture` | Full orchestration — feature, debug, or fix-flow end-to-end |
| `/dark-factory:init` | Initialize a new project with dark factory |
| `/dark-factory:update` | Update the plugin to the latest version |
