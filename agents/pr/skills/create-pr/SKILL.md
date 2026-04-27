---
name: create-pr
description: "Opens a pull request on GitHub using a fix already applied to the working tree. Provides all scripts needed to manage the full PR lifecycle: open, CI checks, comment resolution, and merge."
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
   git add --all
   git commit -m "<short title from bug explanation>"
   ```

3. Push the branch and open the PR:
   ```bash
   git push -u origin HEAD
   # Always write the body to a temp file — never pass it inline with --body.
   # Inline bodies fail with "Parser aborted" when the content is large.
   cat > /tmp/pr-body.md << 'EOF'
   <body content here>
   EOF
   gh pr create --title "<type>(<scope>): <description>" --body-file /tmp/pr-body.md
   ```

## PR Title Format

Use `<type>(<scope>): <description>` — imperative mood, under 72 characters.

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Maintenance, deps, config |
| `docs` | Documentation only |
| `refactor` | Code change that isn't a fix or feature |
| `test` | Adding or updating tests |
| `ci` | CI/CD pipeline changes |
| `perf` | Performance improvement |
| `style` | Formatting, whitespace (no logic change) |
| `revert` | Reverting a previous commit |

**Examples:**
- `feat(pr-agent): add branch deletion after merge`
- `fix(ci): handle quota exhaustion as a passing check`
- `chore(settings): allow git and gh commands without prompting`

## Scripts

| What it does | Script |
|---|---|
| Watch CI checks until complete | `gh pr checks <PR_URL> --watch` |
| Get failed CI run logs | `gh pr checks <PR_URL> --fail-fast` then `gh run view <run-id> --log-failed` |
| View PR comments | `gh pr view <PR_URL> --comments` |
| Get PR node ID | `gh api graphql -f query='query($owner:String!,$repo:String!,$number:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$number){id}}}' -F owner="{owner}" -F repo="{repo}" -F number=<PR_NUMBER> --jq '.data.repository.pullRequest.id'` |
| List unresolved review threads | `gh api graphql -f query='query($id:ID!){node(id:$id){... on PullRequest{reviewThreads(first:50){nodes{id isResolved comments(first:10){nodes{body}}}}}}}' -F id="$PR_ID"` |
| Resolve a review thread | `gh api graphql -f query='mutation($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{isResolved}}}' -F threadId="<THREAD_ID>"` |

## Rules

- Only commit files that are part of the fix. Do not commit unrelated changes.
- If there are no staged changes, stop and report the problem to the caller — do not open an empty PR.
- After addressing review threads, resolve each one using the resolve script before re-checking CI.
