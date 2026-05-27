---
name: git-c-worktree-subagent
description: "All git operations inside sub-agents that run in an isolated worktree must use git -C WORK_DIR to avoid silently defaulting to the main worktree CWD and committing to the wrong branch."
user-invocable: false
---
## When to use

Whenever writing or reviewing a sub-agent (feature-agent, debugger-agent, repair-implementation-agent or any agent invoked by dark-factory-agent) that issues git commands — add, commit, push, checkout, log, status, etc.

The Bash tool in a sub-agent does not inherit the orchestrator's working directory. If a sub-agent's CWD resolves to the original project root (main worktree) instead of WORK_DIR, any `git commit` will land on the branch that is currently checked out there — typically `main` — not the feature branch.

## Steps

1. In every sub-agent that receives `workDir` (or equivalent), require that all git commands be scoped with `-C`:
   ```bash
   git -C "$WORK_DIR" add -A
   git -C "$WORK_DIR" commit -m "feat: ..."
   git -C "$WORK_DIR" push origin feature/<taskName>
   git -C "$WORK_DIR" status
   git -C "$WORK_DIR" log --oneline -5
   ```

2. Never use bare `git <subcommand>` inside a sub-agent when the desired repo is a worktree at a specific path. Even if the agent appears to be "inside" the worktree, the Bash tool's CWD cannot be assumed.

3. When reviewing a sub-agent for correctness, grep for bare `git ` lines (no `-C` flag) as an automated smell:
   ```bash
   grep -n '\bgit \b' agents/<agent-dir>/agents/<agent>.md | grep -v 'git -C'
   ```

4. In the orchestrator that spawns the sub-agent, pass `workDir` explicitly in the invocation payload, and document that the sub-agent must use `-C workDir` for all git calls.

## gh CLI workaround (no -C flag)

Unlike `git`, the `gh` CLI does **not** support a `-C <dir>` flag. It resolves the repository from the process working directory. When sub-agents need to run `gh pr view`, `gh pr create`, or any other `gh` command scoped to a specific worktree, they must `cd` into `workDir` first:

```bash
# WRONG — gh resolves the repo from CWD, not from the -C flag
cd "$workDir" && gh pr view --json url --jq '.url'   # correct
gh pr view --json url --jq '.url'                     # wrong if CWD is main repo
```

In agent pseudocode:
```
existingPr = bash("cd \"$workDir\" && gh pr view --json url --jq '.url' 2>/dev/null || echo ''")
```

This matters most in pr-agent when checking whether an existing PR is open on the feature branch. Without `cd "$workDir"`, `gh pr view` checks the main repo's current branch (typically `main`), not the feature branch in the isolated worktree.

## Notes

- `git -C <path>` is equivalent to `cd <path> && git` but does not mutate the process CWD, making it safe to use in a Bash tool call that might be followed by other shell operations.
- `gh` has no `-C` equivalent — always use `cd "$workDir" && gh ...` instead.
- The companion pattern for detecting when this rule was violated at runtime is the branch-drift guard — see skill `branch-drift-guard`.
- This rule applies even when the sub-agent's instruction says "you are already inside WORK_DIR". The Bash tool's CWD is determined by the LLM runtime, not by prose instructions.
- If a sub-agent truly cannot use `-C` (e.g., it must run a script that calls git internally), ensure the script itself is passed WORK_DIR and uses it as `--git-dir` / `--work-tree` or changes directory internally before any git calls.
