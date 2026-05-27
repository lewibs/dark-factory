#!/usr/bin/env bash
# reset.sh — Reset to main branch in the main worktree and pull latest code
# This script provides a quick way to return to the main state after feature development

set -euo pipefail

# Get the git root
if ! GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
  echo "reset.not-git-repo: Current directory is not in a git repository" >&2
  exit 1
fi

echo "reset | git-root | $GIT_ROOT" >&2

# Find the main worktree by listing all worktrees and finding the one on main branch
# The main worktree is either explicitly checked out on 'main' or is the primary worktree
MAIN_WORKTREE=""

while IFS= read -r line; do
  # Each line format: <path> <ref>
  # Example: /home/user/project (main)
  #          /home/user/project-feature feature/foo
  if [[ $line =~ ^(.*)[[:space:]]+\(([^)]+)\)$ ]]; then
    path="${BASH_REMATCH[1]}"
    ref="${BASH_REMATCH[2]}"
    
    if [[ "$ref" == "main" || "$ref" == "master" ]]; then
      MAIN_WORKTREE="$path"
      break
    elif [[ ! "$ref" =~ ^[a-z]/ ]]; then
      # Fallback: if it's detached or unknown, might be the main worktree
      # But we prefer explicit main/master match above
      if [[ -z "$MAIN_WORKTREE" ]]; then
        MAIN_WORKTREE="$path"
      fi
    fi
  fi
done < <(git -C "$GIT_ROOT" worktree list 2>/dev/null || true)

if [[ -z "$MAIN_WORKTREE" ]]; then
  echo "reset.no-main-worktree: Could not find the main worktree" >&2
  exit 1
fi

echo "reset | main-worktree | $MAIN_WORKTREE" >&2

# Navigate to the main worktree
if ! cd "$MAIN_WORKTREE" 2>/dev/null; then
  echo "reset.no-main-worktree: Could not navigate to main worktree at $MAIN_WORKTREE" >&2
  exit 1
fi

# Check out main branch
if ! git checkout main 2>&1 | grep -v "^Switched to branch\|^Already on"; then
  echo "reset.checkout-failed: Failed to check out main branch" >&2
  exit 1
fi

echo "reset | checkout | main" >&2

# Pull latest code
if ! git pull origin main 2>&1 | grep -v "^Already up to date\|^Fast-forward\|^Merge made"; then
  echo "reset.pull-failed: Failed to pull latest code from origin main" >&2
  exit 1
fi

echo "reset | pull | success" >&2
echo "reset.success: Reset complete. Returned to main branch in $MAIN_WORKTREE and pulled latest code." >&2
