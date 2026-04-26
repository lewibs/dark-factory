#!/usr/bin/env bash
set -euo pipefail

# Run from anywhere inside a git repository.
# Usage: bash prep-feature-dir.sh <task-name>
# Prints: WORK_DIR=<absolute-path-to-worktree>

TASK_NAME="${1:-}"
if [ -z "$TASK_NAME" ]; then
    echo "Error: task name required. Usage: $0 <task-name>" >&2
    exit 1
fi

GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "Error: not inside a git repository." >&2; exit 1; }

PROJECT_NAME=$(basename "$GIT_ROOT")
WORKTREE_NAME="${PROJECT_NAME}-${TASK_NAME}"
WORK_DIR="${GIT_ROOT}/../${WORKTREE_NAME}"

if git -C "$GIT_ROOT" worktree list | grep -qF "$WORKTREE_NAME"; then
    echo "WORK_DIR=${WORK_DIR}"
    exit 0
fi

git -C "$GIT_ROOT" pull origin main || { echo "Error: git pull failed." >&2; exit 1; }
git -C "$GIT_ROOT" worktree add "$WORK_DIR" -b "feature/${TASK_NAME}" || { echo "Error: git worktree add failed." >&2; exit 1; }

echo "WORK_DIR=${WORK_DIR}"
