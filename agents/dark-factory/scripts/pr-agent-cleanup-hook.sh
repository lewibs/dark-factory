#!/usr/bin/env bash
# pr-agent-cleanup-hook.sh
# Triggered when pr-agent stops. Checks out main and cleans up the worktree.
# Reads WORK_DIR from /tmp/dark-factory-work-dir pointer file since env vars
# may not be visible in hook processes.

set -e

POINTER_FILE="/tmp/dark-factory-work-dir"

# Read WORK_DIR from pointer file
if [ ! -f "$POINTER_FILE" ]; then
    echo "WARNING: Pointer file $POINTER_FILE not found. Skipping cleanup." >&2
    exit 0
fi

WORK_DIR=$(cat "$POINTER_FILE" 2>/dev/null || echo "")
if [ -z "$WORK_DIR" ]; then
    echo "WARNING: WORK_DIR not found in $POINTER_FILE. Skipping cleanup." >&2
    exit 0
fi

# Extract task name from WORK_DIR path (e.g., /path/dark_factory-move-cleanup-to-pr-agent-hook -> move-cleanup-to-pr-agent-hook)
TASK_NAME=$(basename "$WORK_DIR" | sed 's/^dark[_-]factory[_-]//')

if [ -z "$TASK_NAME" ]; then
    echo "WARNING: Could not extract TASK_NAME from WORK_DIR. Skipping cleanup." >&2
    exit 0
fi

# Determine the project dir (parent of the worktree)
PROJECT_DIR=$(dirname "$WORK_DIR")

# Checkout main in the project directory
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "Checking out main in project directory: $PROJECT_DIR" >&2
    git -C "$PROJECT_DIR" checkout main 2>/dev/null || echo "WARNING: Failed to checkout main" >&2
else
    echo "WARNING: Project directory $PROJECT_DIR is not a git repo. Skipping checkout." >&2
fi

# Run cleanup-worktree.sh with the extracted WORK_DIR and TASK_NAME
echo "Running cleanup for worktree: $WORK_DIR, task: $TASK_NAME" >&2
bash "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/cleanup-worktree.sh" "$WORK_DIR" "$TASK_NAME" || echo "WARNING: cleanup-worktree.sh failed" >&2

# Clean up the pointer file
rm -f "$POINTER_FILE" 2>/dev/null || true

exit 0
