#!/usr/bin/env bash
# Usage: bash cleanup-worktree.sh <work-dir> <task-name>
# Always exits 0 — failures are warnings only.

WORK_DIR="${1:-}"
TASK_NAME="${2:-}"

if [ -z "$WORK_DIR" ] || [ -z "$TASK_NAME" ]; then
    echo "Error: usage: $0 <work-dir> <task-name>" >&2
    exit 1
fi

git worktree remove "$WORK_DIR" --force 2>/dev/null || echo "WARNING: worktree remove failed for ${WORK_DIR} — manual cleanup may be needed." >&2
git branch -D "feature/${TASK_NAME}" 2>/dev/null || echo "WARNING: branch delete failed for feature/${TASK_NAME} — manual cleanup may be needed." >&2

exit 0
