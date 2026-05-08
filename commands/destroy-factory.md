# destroy-factory

Closes the current terminal/factory session. Only terminates the terminal this command is run from — no other terminals are affected.

## Usage

```
/dark-factory:destroy-factory
```

## Description

Cleanly closes the current Claude terminal session by stopping its own vte-spawn cgroup scope and terminating the ancestor `claude` process. Does not affect any other terminals or sessions.

## Platform

Linux only. Designed for GNOME terminal and other systems using systemd cgroup scopes.

## Implementation

Calls `scripts/close-factory.sh` to stop the current terminal's vte-spawn cgroup scope and terminate the ancestor `claude` process.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/destroy-factory.sh"
```

## Flows

- `destroy-factory.success` — Terminal closed cleanly; command exits with code 0.
