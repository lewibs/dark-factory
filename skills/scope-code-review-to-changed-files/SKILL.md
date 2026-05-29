---
name: scope-code-review-to-changed-files
description: "Pass changedFiles to code-review-orchestrator-agent so reviewers only read files that were actually modified, instead of scanning the entire project root — critical for debug and narrow-scope fix pipelines."
user-invocable: false
---
## When to use

Any time an orchestrating agent (debug-command-agent, hotfix pipeline, etc.) invokes `code-review-orchestrator-agent` after a change that touched a known, bounded set of files. Without this, high-level-review-agent and low-level-review-agent both read ALL source files under `codePath`, which adds 4-6 minutes of unnecessary work for small fixes.

Concrete triggers:
- After a bug fix that touched 1-5 files
- After a narrowly scoped refactor where changed files are known
- Any pipeline where you can compute `git diff --name-only HEAD~1` before invoking code review

## Steps

1. Before invoking code-review-orchestrator-agent, compute the list of changed files:
   ```
   CHANGED_FILES = run `git diff --name-only HEAD~1` in workDir
   ```
   This gives a newline-separated list of relative file paths.

2. Pass the changed files list to code-review-orchestrator-agent as `changedFiles`:
   ```
   invoke code-review-orchestrator-agent({
     codePath: <project root>,
     changedFiles: CHANGED_FILES,
     ...other params
   })
   ```

3. Inside code-review-orchestrator-agent (and the high-level/low-level reviewers it spawns), when `changedFiles` is provided and non-empty, read only those specific files instead of all files under `codePath`.

4. When `changedFiles` is null or empty, fall back to reading all files under `codePath` (full review, as before).

## Notes

- `git diff --name-only HEAD~1` works when all changes are in a single commit. If changes span multiple commits, use `git diff --name-only <base-sha>...HEAD` or derive changed files from the plan.
- The `codePath` parameter should still be the project root so reviewers have context for imports and cross-file references — only the set of files actually read should be narrowed.
- This pattern is most impactful on debug pipelines. Feature manufacture runs that touch many files across the codebase may not benefit as much and can continue passing `codePath` only.
- If the changed files list is very large (>20 files), consider whether a full review is appropriate instead.
