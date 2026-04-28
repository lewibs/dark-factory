---
name: fix-loop-accumulate-commits-single-pr
description: "Use this skill when designing any iterative fix loop (e.g., ralph-fix-and-push) to accumulate all fixes as local git commits on the current feature branch and create a single PR only after the loop exits successfully."
user-invocable: false
---
## When to use

Any time you write or modify an agent that:
- Iterates over repeated fix attempts (debug → fix → re-test → repeat)
- Previously created a PR per iteration

The correct pattern is to commit each fix locally and create ONE PR after all bugs are resolved.

## Steps

1. At the start of the agent, initialize a list to track bug doc file paths:
   ```
   bugDocPaths = []
   ```

2. After each fix attempt inside the loop, commit locally — do NOT spawn pr-agent yet:
   ```
   git add -A
   git commit -m "fix: resolve bug from docs/bugs/$(basename $bugDocPath)"
   ```
   For partial fixes (flow still failing), use a descriptive message:
   ```
   git commit -m "fix: attempt fix from docs/bugs/$(basename $bugDocPath)"
   ```

3. Append the bug doc path to the tracking list on every iteration:
   ```
   bugDocPaths.append(bugDocPath)
   ```

4. After the loop exits (flow passes green), format all bug doc paths as markdown links and pass them to pr-agent in the PR body:
   ```
   bugFileLinks = format_pr_body(bugDocPaths)
   prResult = spawn pr-agent(
     taskDescription = "Fix integration flow: accumulated fixes from: " + bugFileLinks,
     prBody = "## Fixes\n\nThis PR accumulates all bug fixes for the integration flow:\n" + bugFileLinks
   )
   ```

5. Return a single `pr_url` (not an array) plus `bugFiles` from the agent:
   ```
   return { pr_url: prResult.pr_url, merged: prResult.merged, bugFiles: bugDocPaths, allGreen: true }
   ```

6. Update the agent's `allowed-tools` front-matter to include the git subcommands used:
   ```yaml
   allowed-tools: Bash(bash *), Bash(find *), Bash(git add *), Bash(git commit *), Bash(git checkout *), Bash(git branch *)
   ```

## Notes

- The instinct to create a PR per iteration is wrong for iterative fix loops. It creates noisy PR history and blocks the flow until each PR is merged before the next iteration can push.
- Only call pr-agent once, after the loop exits. The single PR will contain all accumulated commits from every iteration.
- If the loop gets stuck (same root cause repeats with no progress), call PushNotification + AskUserQuestion before aborting — do not create a PR for a stuck loop.
- The output contract changes from `pr_urls: string[]` to `pr_url: string` when migrating from per-iteration to single-PR. Any upstream orchestrator that previously reported a list of PR URLs must be updated to report the single URL.
- This pattern was introduced in the 2026-04-28 fix-flow-single-branch change to `ralph-fix-and-push.md`.
