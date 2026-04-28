---
description: "Open a new gnome-terminal window running claude /remote-control"
---

Opens a new terminal in the current working directory and launches Claude in remote-control mode. Useful for spawning parallel factory processing sessions.

## Usage

```bash
/dark-factory:spawn-factory [terminal-name]
```

### Parameters

- `terminal-name` (optional): Name for the remote control session. Defaults to "dark factory" if not provided.

## Examples

```bash
# Launch with default name
/dark-factory:spawn-factory

# Launch with custom name
/dark-factory:spawn-factory "build-feature-1"
```

## Returns

```json
{
  "status": "success",
  "message": "Terminal launched"
}
```

Or on error:

```json
{
  "status": "error",
  "message": "<error description>"
}
```

## Implementation

This command:
1. Accepts an optional terminal name parameter (defaults to "dark factory")
2. Resolves the current working directory
3. Executes `gnome-terminal` asynchronously with the working directory and Claude remote-control command
4. Returns immediately with success status

The new terminal runs: `claude "/remote-control <name>"`

See `scripts/reopen-remote-control.sh` for the underlying pattern.
