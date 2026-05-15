---
name: fuzzy-match-open-pr
description: "Find an open GitHub PR that likely corresponds to a task description using keyword scoring, to support PR reuse before creating a new branch."
user-invocable: false
---
## When to use

Before creating a new branch for a task, check whether an open PR already exists for the same work. This avoids duplicate PRs and allows continued work on an existing branch. Invoke this pattern at the start of the branch-preparation step whenever the task might be a re-run or continuation of prior work.

## Steps

1. Normalize the task description to lowercase keywords, strip punctuation:
   ```bash
   keywords=$(echo "$taskDescription" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9 ' ' ' | tr -s ' ')
   ```

2. Fetch open PRs from GitHub with title, branch, url, and number. Gracefully handle auth/network failure:
   ```bash
   prs=$(gh pr list --state open --limit 50 --json title,headRefName,url,number --order updated --sort desc 2>/dev/null) || {
     echo "# Warning: Could not fetch open PRs. Proceeding with new branch." >&2
     exit 0
   }
   ```

3. Pass keywords via environment variable (not shell interpolation) to avoid injection, then score each PR with python3 inline:
   ```bash
   export _DF_KEYWORDS="$keywords"
   best=$(echo "$prs" | python3 -c "
   import sys, json, os
   data = json.loads(sys.stdin.read().strip())
   keywords = set(os.environ.get('_DF_KEYWORDS', '').split())
   best = None; best_score = 0; best_index = float('inf')
   for idx, pr in enumerate(data):
       candidate = (pr['title'] + ' ' + pr['headRefName']).lower()
       score = sum(1 for kw in keywords if kw in candidate and len(kw) >= 2)
       if score >= 2 and (score > best_score or (score == best_score and idx < best_index)):
           best_score = score; best = pr; best_index = idx
   if best:
       print(f\"BRANCH={best['headRefName']}\")
       print(f\"URL={best['url']}\")
       print(f\"TITLE={best['title']}\")
   ")
   ```
   Score threshold of 2 keywords (each >= 2 chars) balances recall vs. false positives. On tie, prefer the most recently updated PR (first in list since `--sort desc`).

4. Parse the output and, if a match was found, ask the user whether to reuse the branch or create a fresh one:
   ```
   EXISTING_BRANCH = extract BRANCH= line
   if EXISTING_BRANCH is not empty:
     answer = AskUserQuestion("Reuse existing branch or create new?", options: ["Reuse existing branch", "Create new branch"])
   ```

5. If reuse is chosen, derive the worktree name by stripping any `<prefix>/` from the branch name (the part up to and including the first `/`):
   ```
   existingTaskName = EXISTING_BRANCH with leading "<prefix>/" stripped
   WORKTREE_NAME = PROJECT_NAME + "-" + existingTaskName
   WORK_DIR = GIT_ROOT + "/../" + WORKTREE_NAME
   ```
   Then add the worktree if it does not already exist, or verify branch alignment if it does:
   ```bash
   git -C "$GIT_ROOT" worktree add "$WORK_DIR" "$EXISTING_BRANCH"
   ```

## Notes

- Always pass keyword strings via environment variables, never via shell interpolation into python3 `-c` strings — task descriptions may contain quotes or special characters that break the command.
- The minimum keyword length filter (`len(kw) >= 2`) avoids noise from stop words like "a", "i".
- If `gh pr list` fails (network error, not authenticated), exit 0 and let the calling agent fall back to creating a new branch — do not block the flow.
- When a worktree already exists for the reused branch, verify the checked-out branch matches `EXISTING_BRANCH` before proceeding. If it does not match, report an error and stop — do not silently continue on the wrong branch.
- The drift guard must use the full `branchRef` (e.g. `bugfix/foo` or `plain-slug`) rather than hardcoding `feature/<taskName>` when a reused branch is involved. See skill `branch-drift-guard`.
