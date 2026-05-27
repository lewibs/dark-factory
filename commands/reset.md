---
description: "Return to the main branch in the main worktree and pull the latest code. Useful for cleaning up after feature work."
---

Reset your git repository to the main branch in the main worktree and pull the latest code.

## Usage

```bash
/reset
```

## Description

This command:
1. Determines the current git root
2. Finds the main worktree (the primary worktree without a feature branch suffix)
3. Navigates to that worktree
4. Checks out the `main` branch
5. Pulls the latest code from `origin main`
6. Notifies you when complete

Useful after feature development to quickly return to a clean main state without manual git operations.

## Implementation

```bash
bash "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/reset.sh"
```

## Flows

- `reset.success` — Successfully returned to main, checked out main branch, and pulled latest code
- `reset.not-git-repo` — Current directory is not in a git repository
- `reset.no-main-worktree` — Could not find the main worktree
- `reset.checkout-failed` — Failed to check out main branch (e.g., dirty working directory)
- `reset.pull-failed` — Failed to pull latest code (e.g., merge conflicts)
