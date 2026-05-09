---
name: branch-drift-guard
description: "After a worker agent returns in an orchestrator, verify the feature branch is ahead of main to detect cases where the worker committed to the wrong branch or failed to commit at all."
user-invocable: false
---
## When to use

Immediately after any worker agent (feature-agent, debugger-agent, repair-agent) returns control to the dark-factory orchestrator, and before proceeding to code review or PR steps.

This guard catches the class of bug where a sub-agent runs `git commit` without an explicit `-C WORK_DIR` or `--work-tree` flag and the commit lands on the wrong branch (e.g., main) because the CWD defaults to the parent worktree.

## Steps

1. After the worker agent returns, compute the feature branch name:
   ```
   featureBranch = "feature/" + taskName
   ```

2. Run a scoped git log to check for commits ahead of main:
   ```bash
   git -C "$WORK_DIR" log main..feature/<taskName> --oneline
   ```

3. If the output is empty (no commits ahead), the worker either committed to the wrong branch or did not commit at all. Do not proceed:
   ```
   rm -f /tmp/dark-factory-work-dir
   run cleanup(WORK_DIR)
   report error: "Branch-drift guard failed: feature/<taskName> has no commits ahead of main.
     The worker agent may have committed to the wrong branch or failed to commit at all.
     Halting before code review to prevent opening a PR with no changes."
   STOP
   ```

4. If the output is non-empty, the feature branch has the expected commits — continue to code review.

## Notes

- Always use `git -C "$WORK_DIR"` (not a bare `git`) so the command targets the isolated worktree, not whatever the orchestrator's CWD happens to be.
- This guard should run even when the worker returns `status == "done"` — a successful return does not guarantee the commit landed on the correct branch.
- The root cause of branch drift is sub-agents issuing git commands without `-C WORK_DIR`, causing git to resolve the repo from the ambient shell CWD, which may point to the main worktree. See skill `git-c-worktree-subagent` for the companion fix.
- If the project uses a different default branch name (e.g., `master`), substitute it for `main` in the log range.
