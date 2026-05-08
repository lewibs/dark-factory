# destroy-factories

Terminates all other running Claude / dark-factory terminal sessions.

## Usage

```
/dark-factory:destroy-factories
```

## Description

Scans all running terminal emulator processes for those that have a `claude` descendant process. Kills each one (excluding the terminal running this command).

Safe by design: only terminals whose process tree contains a `claude` descendant are targeted. Unrelated terminals are never touched.

## Platform

Linux only. Requires at least one of: `gnome-terminal`, `x-terminal-emulator`, `xterm`, or `konsole`.

## Implementation

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/destroy-factories.sh"
```

## Flows

- `destroy-factories.success` — Claude terminals found and killed; command exits cleanly.
- `destroy-factories.none-found` — No Claude terminals found; command exits cleanly (no kills needed).
- `destroy-factories.kill-failed` — Kill fails for one or more PIDs; warns to stderr, continues.
