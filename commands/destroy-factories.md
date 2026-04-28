# destroy-factories

Terminates all other running Claude / dark-factory terminal sessions and spawns one fresh factory terminal, leaving the user with exactly one active terminal.

## Usage

```
/dark-factory:destroy-factories [name]
```

## Description

Scans all running terminal emulator processes for those that have a `claude` descendant process. Kills each one (excluding the terminal running this command), then opens a new terminal running `claude "/remote-control <name>"`.

Safe by design: only terminals whose process tree contains a `claude` descendant are targeted. Unrelated terminals are never touched.

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `name` | `dark factory` | Remote-control session name for the new terminal |

## Platform

Linux only. Requires at least one of: `gnome-terminal`, `x-terminal-emulator`, `xterm`, or `konsole`.

## Implementation

```bash
bash scripts/destroy-factories.sh "dark factory"
```

## Flows

- `destroy-factories.success` — Claude terminals found and killed; new factory terminal spawned.
- `destroy-factories.none-found` — No Claude terminals found; new factory terminal spawned (no kills).
- `destroy-factories.kill-failed` — Kill fails for one or more PIDs; warns to stderr, continues to spawn.
- `destroy-factories.spawn-failed` — Terminal spawn fails; prints error to stderr and exits non-zero.
