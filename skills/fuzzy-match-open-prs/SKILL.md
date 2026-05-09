---
name: fuzzy-match-open-prs
description: "When an orchestrator needs to avoid duplicate PRs, fuzzy-match a task description against open PR titles and branch names using keyword scoring via a shell script."
user-invocable: false
---
## When to use

Before creating a new feature branch, check whether an open PR already covers the same work. This prevents duplicate PRs and lets the agent push to the existing PR instead of opening a new one.

## Steps

1. Create a helper script (e.g. `find-related-pr.sh <taskDescription>`) that:
   - Normalizes the task description to lowercase keywords, strips punctuation:
     ```bash
     keywords=$(echo "$taskDescription" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9 ' ' ' | tr -s ' ')
     ```
   - Fetches open PRs with `gh pr list --state open --limit 50 --json title,headRefName,url 2>/dev/null || exit 0`
   - Guards against empty/null JSON before passing to python3 (avoid JSONDecodeError):
     ```bash
     if [ -z "$prs" ] || [ "$prs" = "null" ]; then exit 0; fi
     ```
   - Passes keywords via environment variable (not shell interpolation) to avoid injection:
     ```bash
     export _DF_KEYWORDS="$keywords"
     ```
   - Scores each PR: count keyword hits (len > 2) in `title + headRefName`. Emit `BRANCH=`, `URL=`, `TITLE=` lines if `score >= 2`.

2. In the orchestrator, call the script with `|| ""` so a non-zero exit is treated as no-match:
   ```
   relatedPrOutput = bash("find-related-pr.sh \"$taskDescription\"") || ""
   EXISTING_BRANCH = extract BRANCH=<value> from relatedPrOutput (or empty)
   ```

3. If `EXISTING_BRANCH` is non-empty, present the match to the user via `AskUserQuestion` with options `["Reuse existing branch", "Create new branch"]`.

4. If confirmed, check out the existing branch as a worktree and set `WORK_DIR` accordingly. If declined or no match, fall through to the normal new-branch flow unchanged.

## Notes

- The threshold of `score >= 2` and `len(kw) > 2` balances recall vs. false positives. It can be tuned in the script without touching orchestrator logic.
- Always guard `gh pr list` output against empty strings and `null` before JSON-parsing — `gh` may return empty output or `null` when no PRs exist.
- The script must output machine-parseable `KEY=value` lines on stdout and use stderr-only for diagnostics; the orchestrator greps stdout for the values.
- Reference implementation: `agents/dark-factory/scripts/find-related-pr.sh`
