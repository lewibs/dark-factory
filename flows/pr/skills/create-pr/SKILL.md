---
name: create-pr
description: Opens a pull request on GitHub using a fix already applied to the working tree. Provides all scripts needed to manage the full PR lifecycle: open, CI checks, comment resolution, and merge.
user-invocable: false
---

# create-pr

Open a pull request on GitHub and manage it through to merge.

## Steps

1. Create a new branch for the fix:
   ```bash
   git checkout -b fix/<slug-from-bug-title>
   ```

2. Stage and commit all changes:
   ```bash
   git add -p
   git commit -m "<short title from bug explanation>"
   ```

3. Push the branch and open the PR:
   ```bash
   git push -u origin HEAD
   gh pr create --title "<title>" --body "<description>"
   ```

## Scripts

| What it does | Script |
|---|---|
| Watch CI checks until complete | `gh pr checks <PR_URL> --watch` |
| Get failed CI run logs | `gh pr checks <PR_URL> --fail-fast` then `gh run view <run-id> --log-failed` |
| View PR comments | `gh pr view <PR_URL> --comments` |
| Get PR node ID | `gh api graphql -f query='query($owner:String!,$repo:String!,$number:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$number){id}}}' -F owner="{owner}" -F repo="{repo}" -F number=<PR_NUMBER> --jq '.data.repository.pullRequest.id'` |
| List unresolved review threads | `gh api graphql -f query='query($id:ID!){node(id:$id){... on PullRequest{reviewThreads(first:50){nodes{id isResolved comments(first:10){nodes{body}}}}}}}' -F id="$PR_ID"` |
| Resolve a review thread | `gh api graphql -f query='mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{isResolved}}}' -F threadId="<THREAD_ID>"` |
| Squash merge the PR | `gh pr merge <PR_URL> --squash --auto` |

## Rules

- Only commit files that are part of the fix. Do not commit unrelated changes.
- If there are no staged changes, stop and report the problem to the caller — do not open an empty PR.
- After addressing review threads, resolve each one using the resolve script before re-checking CI.
