---
name: pr-agent-does-not-merge
description: "Use this skill when designing any flow that calls pr-agent — pr-agent stops at status: ready and does not merge; the caller is responsible for deciding when and how to merge."
user-invocable: false
---
## When to use

Any time you write or update an agent that calls `pr-agent`, or any time you design a new PR-adjacent flow and need to know what pr-agent does and does not do.

## Steps

1. Expect `pr-agent` to return `{ pr_url, status: "ready" }` — not `{ pr_url, merged: true }`. The PR will be open, CI-green, and thread-free, but not merged.

2. If the calling flow needs a merge, the caller must issue it explicitly after receiving `status: "ready"`:
   ```bash
   gh pr merge <PR_URL> --squash --delete-branch
   ```

3. Do **not** add merge logic back into `pr-agent.md`. The merge boundary is intentional: it lets callers decide merge strategy (squash, merge commit, rebase) and timing (e.g., waiting for additional approvals, release windows).

4. Do **not** add `gh pr merge` to `pr-agent`'s `allowed-tools` front-matter. The absence of that tool is the enforcement mechanism.

5. After merge the caller should also clean up locally:
   ```bash
   git checkout main && git pull
   git branch -d <branch-name>
   ```

## Notes

- Before this boundary was established, `pr-agent` included a squash-merge-and-delete step (step 6-8 in the old numbered list). That step was removed in the 2026-04-26 PR-agent CI comment loops refactor. Do not re-introduce it.
- The `create-pr` skill's Scripts table also no longer contains the squash-merge row — it was removed at the same time. If you need that script, issue it from the caller, not from `create-pr`.
- `resolve-pr-issue` is also unaffected by this boundary — it only fixes CI failures and review threads; it does not merge.
