---
name: install-plugin
description: Install or update the dark-factory plugin in Claude Code.
user-invocable: true
---

## Install (one-time)

```bash
# 1. Register the local repo as a marketplace source (run from repo root)
claude plugin marketplace add "$(pwd)"

# 2. Install the plugin
claude plugin install dark-factory
```

## Update (after pulling new changes)

```bash
git pull
# Re-register local repo as marketplace source, then update
claude plugin marketplace add "$(pwd)"
claude plugin update dark-factory
```

## Error handling

- If `claude plugin marketplace add` fails with "path not found" or "already registered differently", verify you are running the command from inside the correct repo root directory and that the path is valid.
- If `claude plugin update` exits non-zero, check `claude plugin list` to confirm the plugin name and re-run `claude plugin marketplace add "$(pwd)"` before retrying.

## Verify

```bash
claude plugin list
```

## Available commands after install

| Command | Description |
|---|---|
| `/dark-factory:manufacture` | Full orchestration — feature, debug, or fix-flow end-to-end |
| `/dark-factory:repair` | Lightweight targeted fix — no planning phase |
| `/dark-factory:init` | Initialize a new project with dark factory |
| `/dark-factory:update` | Update the plugin to the latest version |
