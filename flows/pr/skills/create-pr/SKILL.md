---
name: create-pr
description: Opens a pull request on GitHub using a fix already applied to the working tree and /tmp/bug-explanation.md as the PR description. Used by pr-agent inside fix-flow-orchestrator.
user-invocable: false
---

# create-pr

Open a pull request on GitHub using the fix already applied to the working tree and the bug explanation as the PR description.

## Steps

1. Read `/tmp/bug-explanation.md` — this is the PR body verbatim.

2. Create a new branch for the fix:
   ```bash
   git checkout -b fix/<slug-from-bug-title>
   ```

3. Stage and commit all changes:
   ```bash
   git add -p  # review what is being committed
   git commit -m "<short title from bug explanation>"
   ```

4. Push the branch:
   ```bash
   git push -u origin HEAD
   ```

5. Open the PR using `gh pr create`:
   ```bash
   gh pr create \
     --title "<short title from bug explanation>" \
     --body "$(cat /tmp/bug-explanation.md)"
   ```

6. Return the PR URL.

## Rules

- Use the bug explanation title as the PR title.
- Use the full contents of `/tmp/bug-explanation.md` as the PR body — do not summarize or rewrite it.
- Only commit files that are part of the fix. Do not commit unrelated changes.
- If there are no staged changes, stop and report the problem to the caller — do not open an empty PR.
