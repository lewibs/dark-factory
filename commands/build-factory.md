---
description: "Open a new gnome-terminal window running claude /remote-control"
---

Opens a new terminal in the current working directory and launches Claude in remote-control mode. Useful for spawning parallel factory processing sessions.

## Implementation

This command delegates to `scripts/open-factory.sh`, which handles the cross-platform terminal emulator detection and launching logic.

## Execution

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/build-factory.sh" "${1:-dark factory}"
```
