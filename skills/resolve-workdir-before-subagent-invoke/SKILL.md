---
name: resolve-workdir-before-subagent-invoke
description: "Command agents must resolve the worktree path via git rev-parse --show-toplevel and pass it explicitly to any sub-agent that performs git or gh operations, rather than letting the sub-agent guess from env vars or pointer files."
user-invocable: false
---
## When to use

In any command agent (execute-command-agent, debug-command-agent, repair-command-agent, or similar) that invokes a downstream agent (pr-agent, skill-update-agent, etc.) that needs to operate on the correct isolated worktree. Apply this before every sub-agent invocation that involves file writes, git commits, pushes, or PR operations.

## Steps

1. At the step where you are about to invoke a sub-agent that needs workDir, resolve the worktree root from the running shell — do not read it from an env var or pointer file, which may be stale or unset:
   ```
   WORK_DIR = bash("git rev-parse --show-toplevel")
   ```

2. Pass WORK_DIR explicitly as a parameter in the sub-agent invocation:
   ```
   prResult = invoke pr-agent({ planFilePath, workDir: WORK_DIR })
   invoke skill-update-agent({ planFilePath, workDir: WORK_DIR, taskSummary })
   ```

3. Never rely on the sub-agent to infer workDir from `$DARK_FACTORY_WORK_DIR` or `/tmp/dark-factory-work-dir` when the calling agent has the correct path available — those fallbacks exist only for agents that are invoked without a caller that knows the path.

## Notes

- `git rev-parse --show-toplevel` returns the absolute root of the worktree that the current process's CWD belongs to. In an isolated worktree at `/path/to/repo-feature-foo`, it returns that path exactly.
- This is distinct from `$DARK_FACTORY_WORK_DIR` (an env var set at worktree creation time) and `/tmp/dark-factory-work-dir` (a pointer file fallback). Those mechanisms are for agents that lack a calling agent able to supply the path. Prefer the explicit parameter chain when the caller can resolve it.
- The concrete failure mode this prevents: pr-agent runs `gh pr view` without knowing the worktree path, so it checks the main repo's current branch instead of the feature branch, finds no open PR, and creates a duplicate.
- See skill `git-c-worktree-subagent` for the related rule that `gh` commands must `cd "$workDir"` since `gh` has no `-C` flag.
