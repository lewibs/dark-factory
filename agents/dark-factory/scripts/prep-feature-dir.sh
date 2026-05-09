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

# Check if the branch already exists
BRANCH_NAME="feature/${TASK_NAME}"
if git -C "$GIT_ROOT" branch --list "$BRANCH_NAME" | grep -qF "$BRANCH_NAME"; then
    # Branch exists; check if it's currently checked out in any worktree
    if git -C "$GIT_ROOT" worktree list --porcelain | grep -qF "branch refs/heads/$BRANCH_NAME"; then
        echo "Error: Branch $BRANCH_NAME is already checked out in a worktree. Remove the existing worktree first or choose a different taskName." >&2
        exit 1
    fi
    # Branch exists but is not checked out; use safe delete to avoid losing unmerged commits
    if ! git -C "$GIT_ROOT" branch -d "$BRANCH_NAME" 2>/dev/null; then
        echo "Error: Branch $BRANCH_NAME has unmerged commits and cannot be safely deleted. Merge or manually delete the branch before retrying." >&2
        exit 1
    fi
fi

git -C "$GIT_ROOT" pull origin main || { echo "Error: git pull failed." >&2; exit 1; }
git -C "$GIT_ROOT" worktree add "$WORK_DIR" -b "$BRANCH_NAME" || { echo "Error: git worktree add failed." >&2; exit 1; }

echo "WORK_DIR=${WORK_DIR}"
