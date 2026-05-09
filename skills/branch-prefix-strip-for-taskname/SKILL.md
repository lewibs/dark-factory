---
name: branch-prefix-strip-for-taskname
description: "When re-entering an existing branch (e.g. feature/foo, bugfix/foo), strip the leading prefix and slash before using the value as a taskName slug — downstream tools reject slashes."
user-invocable: false
---
## When to use

Whenever an agent derives a `taskName` or `WORKTREE_NAME` from an existing branch ref that may carry a category prefix (`feature/`, `bugfix/`, `fix/`, `user/`, etc.). Brain-state-manager, cleanup-worktree.sh, and the worktree directory naming convention all expect a plain slug with no slashes.

## Steps

1. Strip any leading `<prefix>/` from the branch name before using it as a slug:
   ```
   # If EXISTING_BRANCH = "feature/add-oauth"  → existingTaskName = "add-oauth"
   # If EXISTING_BRANCH = "bugfix/null-ptr"    → existingTaskName = "null-ptr"
   # If EXISTING_BRANCH = "plain-slug"          → existingTaskName = "plain-slug"
   existingTaskName = EXISTING_BRANCH after stripping everything up to and including the first "/" (if a "/" is present)
   ```
   In bash: `existingTaskName="${EXISTING_BRANCH#*/}"` — but only when a `/` is present; otherwise use the branch name as-is.

2. Use `existingTaskName` (the stripped slug) as `taskName` for all downstream calls:
   - `WORKTREE_NAME = PROJECT_NAME + "-" + existingTaskName`
   - `WORK_DIR = GIT_ROOT + "/../" + WORKTREE_NAME`
   - brain-state-manager `taskName` field
   - cleanup-worktree.sh argument

3. When checking whether the worktree already exists, match on the derived `WORKTREE_NAME`, not on the full branch ref:
   ```bash
   git -C "$GIT_ROOT" worktree list | grep -qE "(^|/)$WORKTREE_NAME( |$)"
   ```

4. After attaching the worktree, verify the checked-out branch matches `EXISTING_BRANCH` to detect silent mismatches:
   ```bash
   actualBranch=$(git -C "$WORK_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)
   if [ "$actualBranch" != "$EXISTING_BRANCH" ]; then
     # report error and STOP — do not silently commit to the wrong branch
   fi
   ```

## Notes

- Branches with multiple slashes (e.g. `user/alice/feature-x`) should still only strip the first segment; `${EXISTING_BRANCH#*/}` produces `alice/feature-x`, which still contains a slash. Apply a second strip or disallow such branches in the fuzzy-match step if they are expected.
- The drift-guard step must use the full `EXISTING_BRANCH` ref (not the stripped slug prefixed with `feature/`) when diffing against main: `git log main..$EXISTING_BRANCH --oneline`.
- This pattern was introduced in `commands/manufacture.md` Step 2 during the 2026-05-09 PR reuse feature to prevent downstream tools from receiving slash-containing taskName values.
