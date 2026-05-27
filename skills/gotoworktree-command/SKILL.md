---
name: gotoworktree-command
description: "How to build a standalone command that finds or creates a git worktree and leaves the user there, separate from the command agents that do the work."
user-invocable: false
---
## When to use

When you need to add a user-facing command that sets up a worktree without doing any feature/debug/repair work. Also use this skill to understand why worktree prep was extracted out of command agents (plan, execute, debug, repair) into a dedicated command.

## Pattern

Worktree lifecycle management (find, create, pull) is handled by a dedicated `gotoworktree-command-agent`, invoked via `/dark-factory:goto`. The four command agents (plan, execute, debug, repair) run in-place — they do NOT call `prep-feature-dir.sh`, `find-related-pr.sh`, or `git worktree add`. They simply use `PROJECT_DIR = bash("git rev-parse --show-toplevel")`.

## Steps

### Creating the goto command

1. Create `commands/goto.md`:
   ```markdown
   ---
   description: "Find or create a git worktree by PR number, task name, or description."
   ---
   Follow the instructions in `agents/dark-factory/agents/gotoworktree-command-agent.md` exactly.
   ```

2. Create `agents/dark-factory/agents/gotoworktree-command-agent.md` with this orchestration:
   ```
   gotoworktree-command-agent(prNumber, taskName, description):

     # Step 1 — validate: at least one input required
     if prNumber is empty AND taskName is empty AND description is empty:
       report error and STOP

     PROJECT_DIR = bash("git rev-parse --show-toplevel")
     PROJECT_NAME = basename(PROJECT_DIR)

     # Step 2 — derive taskName if not yet provided
     if taskName is empty:
       if prNumber is not empty:
         branchName = bash("gh pr view \"$prNumber\" --json headRefName --jq .headRefName")
         taskName = branchName after stripping leading "<prefix>/" (e.g. "feature/foo" → "foo")
       elif description is not empty:
         taskName = slugify(description)   # lowercase, hyphens, ≤30 chars

     # Step 3 — check for existing local worktree
     WORK_DIR = PROJECT_DIR + "/../" + PROJECT_NAME + "-" + taskName
     if WORK_DIR exists and is a git worktree:
       bash("git -C \"$WORK_DIR\" pull origin main 2>/dev/null || git -C \"$WORK_DIR\" pull origin master || true")
       Report: "Worktree ready at: " + WORK_DIR
       STOP

     # Step 4 — check for open PR (by prNumber or description)
     if prNumber is not empty:
       EXISTING_BRANCH = bash("gh pr view \"$prNumber\" --json headRefName --jq .headRefName")
     else:
       relatedPrOutput = bash("bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/find-related-pr.sh\" \"$description\"") || ""
       EXISTING_BRANCH = extract BRANCH= from relatedPrOutput

     if EXISTING_BRANCH is not empty:
       existingTaskName = EXISTING_BRANCH after stripping "<prefix>/"
       WORK_DIR = PROJECT_DIR + "/../" + PROJECT_NAME + "-" + existingTaskName
       if WORK_DIR does not exist:
         bash("git -C \"$PROJECT_DIR\" pull origin main || true")
         bash("git -C \"$PROJECT_DIR\" worktree add \"$WORK_DIR\" \"$EXISTING_BRANCH\"")
       bash("git -C \"$WORK_DIR\" pull origin main 2>/dev/null || git -C \"$WORK_DIR\" pull origin master || true")
       Report: "Worktree ready at: " + WORK_DIR
       STOP

     # Step 5 — create new worktree via prep-feature-dir.sh
     prepOutput = bash("bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/prep-feature-dir.sh\" \"$taskName\"")
     if script fails: report error and STOP
     WORK_DIR = extract WORK_DIR=<value> from prepOutput
     Report: "Worktree ready at: " + WORK_DIR
     STOP
   ```

### Removing worktree prep from an existing command agent

When refactoring a command agent that previously managed its own worktree:

1. Delete the entire PR-reuse block: `find-related-pr.sh` call, `AskUserQuestion`, `USE_EXISTING` branch, `git worktree add`, `prep-feature-dir.sh` call, `WORK_DIR` and `branchRef` derivation.
2. Delete the branch drift guard (`git log main..<branchRef> --oneline`).
3. Delete `cleanup(WORK_DIR, taskName)` calls from error paths.
4. Replace all `WORK_DIR` references in post-execution steps with `PROJECT_DIR`.
5. Add a comment: "The agent assumes it is already running in the correct working directory (worktree). Worktree creation is handled by gotoworktree-command-agent."

## Notes

- The gotoworktree agent does not delegate to other agents and does not run post-execution pipelines (code review, PR, etc.). It simply lands the user in the right directory.
- Always pull main/master into the worktree before reporting the path — so the user starts from a fresh base.
- `pull origin main || pull origin master || true` is the correct fallback pattern; repos vary in default branch name.
- The worktree naming convention is `<PROJECT_NAME>-<taskName>` and is always located at `PROJECT_DIR/../<WORKTREE_NAME>` — consistent with `prep-feature-dir.sh`.
- After the user runs `/dark-factory:goto`, they open a new Claude Code window in `WORK_DIR`, then invoke plan/execute/debug/repair from there.
