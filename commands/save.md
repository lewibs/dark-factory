---
description: "Save current changes by committing and opening/updating a PR. Shortcut to hand off staged work to pr-agent with no code review, doc, or skill steps."
---

# /dark-factory:save Command

## Purpose

The `/dark-factory:save` command commits the current working tree and opens (or updates) a PR in one step, with no code review, doc update, or skill update steps. It is the user-facing shortcut to hand off staged work to pr-agent.

## Input

- `taskDescription` (optional) — description to use as PR body; defaults to git diff summary if absent

## Process

1. Resolve the working directory:
   ```
   workDir = bash("git rev-parse --show-toplevel")
   ```

2. Delegate to pr-agent with task description and working directory:
   ```
   result = invoke pr-agent({
     taskDescription: taskDescription ?? "Save current changes",
     workDir: workDir
   })
   ```

3. Check result status:
   ```
   if result.status != "ready":
     STOP with error result.reason
   ```

4. Report success:
   ```
   Report: "Saved. PR: " + result.prUrl
   STOP
   ```

## Output

- `prUrl` — URL of the opened or updated PR
- Status: Always "ready" (pr-agent stops here; does not merge)

## Error Handling

If pr-agent reports an error (CI failure or comment resolution failure), the user sees the error message and can retry.

## Notes

- pr-agent handles: commit, push, open/update PR, CI watch, comment resolution
- If an existing PR is detected on the branch, it will be updated with new commits
- No manual code review or PR merge required — user receives the PR URL for manual review if needed
