# pr-agent

**Role**: PR lifecycle manager for completed work.

**Model**: Haiku (lightweight model for PR body composition and comment resolution).

**User-Invocable**: No (invoked by dark-factory-agent after all work is complete).

## Overview

The pr-agent manages the complete PR lifecycle for code that has already been implemented, reviewed, and documented. It opens a PR with a comprehensive body, watches CI until it's green, resolves review comments collaboratively, and stops once CI passes and all threads are resolved. Critically, **the agent does not merge** — it stops at "ready" status, leaving the final merge decision to human judgment.

The PR lifecycle is fully automated except for the final merge decision, enabling code to move from implementation through CI and code review without manual intervention while preserving human control over the merge.

## Input

- `planFilePath` (string, nullable) — Path to the plan file; if null, uses taskDescription
- Or `taskDescription` (string) — Plain description of the work if no plan exists
- If neither: uses git diff

## Orchestration Flow (6 Steps)

### Step 0: Check for Existing PR

1. **Runs `gh pr view`** to check if a PR already exists for the current branch
2. **If a PR exists**:
   - Commits all staged changes with a short description (`git -C "$WORK_DIR" add --all && git -C "$WORK_DIR" commit && git -C "$WORK_DIR" push`)
   - Sets `pr_url` to the existing PR URL
   - Does **not** return early — continues to Step 1
3. **If no PR exists**: `pr_url` is left unset; will be set in Step 2

### Step 1: Build PR Body

1. **Reads PR template** from `agents/pr/templates/pr-template.md` for structure
2. **Populates Description section**:
   - If planFilePath provided: extracts summary from plan
   - If taskDescription provided: uses description directly
   - If neither: builds from git diff
3. **Runs tests** (if test suite exists):
   - Detects test runner (pytest, npm test, go test, etc.)
   - Runs full test suite
   - Includes output in "Test Plan" section
   - Omits "Test Plan" section if no test suite found
4. **Writes body** to `/tmp/pr-body.md` (ready for gh cli)

### Step 2: Open PR (conditional)

1. **Only runs if no existing PR was found in Step 0** (`pr_url` is unset)
2. **Delegates to create-pr skill** with `bodyFile: "/tmp/pr-body.md"`
3. Receives `prUrl` back from skill
4. **Writes brain-patch.json** regardless of path (new or existing PR), resolving work dir via pointer file fallback:
   ```json
   {
     "prUrl": "<github PR URL>",
     "notes": ["pr-agent: opened PR at <prUrl>, CI <passed/failed>"]
   }
   ```
   `<prUrl>` is replaced with the actual PR URL; `<passed/failed>` is filled in with the CI result from Step 3.
   Work dir resolution: use `$DARK_FACTORY_WORK_DIR` if set; else read `/tmp/dark-factory-work-dir`; skip silently if both empty.

### Step 3: Watch CI (always runs)

1. **Always runs** — whether the PR was newly created (Step 2) or already existed (Step 0)
2. **Delegates to ci-watch-runner command** with:
   - `prUrl: <the PR URL>`
   - `maxIterations: 5`

3. Command polls PR CI status repeatedly:
   - Checks status at regular intervals
   - Reports when CI is green, yellow (pending), or red (failed)
   - Stops after maxIterations or when status stabilizes

4. **If ciResult.status == "fail"**: returns error, STOPS
   - CI failed; human review of failures required
   - PR remains open for investigation

5. **If ciResult.status == "pass"**: proceeds to Step 4

### Step 4: Resolve Review Comments (always runs)

1. **Always runs** — whether the PR was newly created (Step 2) or already existed (Step 0)
2. **Gets PR node ID**:
   - Uses `gh api graphql` to fetch `pr.id` from prUrl

3. **Delegates to comment-resolution-runner command** with:
   - `prUrl: <the PR URL>`
   - `prNodeId: <the PR node ID>`
   - `maxIterations: 5`

4. Command iterates through review comments:
   - Reads each comment thread
   - Attempts to resolve by responding (if automated resolution applies)
   - Or requests human clarification
   - Marks threads resolved when addressed
   - Stops after maxIterations or when all threads are resolved

5. **If commentResult.status == "failed"**: returns error, STOPS
   - Review comments could not be resolved
   - PR remains open with pending threads

6. **If commentResult.status == "all-resolved"**: all threads resolved, proceeds to Step 5

### Step 5: Return Success

Returns:
```json
{
  "prUrl": "<github PR URL>",
  "status": "ready"
}
```

Status "ready" indicates:
- CI is passing (all checks green)
- All review comment threads are resolved
- PR is ready for merge (but **not merged** by this agent)

## PR Body Template

The PR body is built from `agents/pr/templates/pr-template.md`, which has exactly two sections:

```markdown
## Description

<!-- Paste the full contents of the relevant plan file (docs/plans/<date>-<slug>.md) or bug file (docs/bugs/<date>-<slug>.md) verbatim here. Do not summarise. -->

## Test Plan

<!-- Only include this section if tests were actually run.
     Paste the exact test output (truncated if very long). If no tests exist, delete this section. -->

---
🤖 Generated with [dark factory](https://github.com/lewibs/dark-factory)
```

**Description source**: The `## Description` section is populated with the full, verbatim contents of the plan file or bug doc — not a summary. If neither exists, the git diff is used.

**Test Plan**: Only included when a test suite was actually run. If no tests exist, the section is omitted entirely.

**PR title**: Derived from the create-pr skill using `<type>(<scope>): <description>` format in imperative mood, under 72 characters. Types include feat, fix, chore, docs, refactor, test, ci, perf, style, revert.

## Key Design Rules

1. **Code is already implemented** — Assume fix is complete; don't re-apply
2. **Always use git -C "$WORK_DIR"** — WORK_DIR is injected by pre-hook
3. **Write body to /tmp/pr-body.md** — Use standard gh cli pattern
4. **Delegate CI watching** — Use ci-watch-runner, don't implement watch loop inline
5. **Delegate comment resolution** — Use comment-resolution-runner, don't implement loop inline
6. **Do NOT merge** — Stop at "ready" status; human makes the merge decision
7. **Write brain-patch after PR opens** — Captures prUrl for downstream use
8. **Resolve WORK_DIR via pointer file fallback** — Check `$DARK_FACTORY_WORK_DIR` first; if unset, read `/tmp/dark-factory-work-dir`; skip silently if both empty
9. **Step 0 does NOT return early** — When an existing PR is found, commit+push and set pr_url, then continue; CI watching and comment resolution always run on both the new-PR and existing-PR paths
10. **gh pr create is conditional** — Only called when no existing PR was found in Step 0
11. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase

## Dependencies

- **Skills**: create-pr (opens the PR)
- **Commands**: ci-watch-runner (polls CI status), comment-resolution-runner (resolves review threads)
- **Templates**: agents/pr/templates/pr-template.md

## Tools

- Read, Bash, Write, Edit, Command

## Return Value

**Success**:
```json
{
  "prUrl": "<github PR URL>",
  "status": "ready"
}
```

**Error**:
```json
{
  "message": "<error description>"
}
```

## SubagentStop Hook

When pr-agent finishes, triggers: `${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/pr-agent-cleanup-hook.sh`

This hook checks out `main` in the project directory and removes the worktree via `cleanup-worktree.sh`. It reads `WORK_DIR` from the `/tmp/dark-factory-work-dir` pointer file (since env vars may not be visible in hook processes), then removes the pointer file itself. Metrics are NOT updated here — metrics are updated by dark-factory-agent in a separate step (Step 12) before this cleanup hook runs.

## Integration with dark-factory-agent

1. Called after all other steps (feature/debug, code review, documentation, skills) complete
2. Blocks on CI passing and review threads resolved
3. If returns error: dark-factory-agent logs the PR URL and error, continues to cleanup
4. If returns success: dark-factory-agent reports final success with PR URL

## Why No Merge?

The pr-agent intentionally stops at "ready" (CI green, reviews resolved) and does not merge. This preserves a critical human decision point: merging to main. Even though all automated checks pass, humans should review the final PR before merge. This pattern:
- Maintains code ownership and accountability
- Allows last-minute vetoes or questions
- Provides a natural place to add human documentation/release notes
- Prevents mass-merging of features without awareness

## Error Handling

- If PR creation fails: surfaces error and STOPS
- If CI never stabilizes (yellow for all iterations): returns failure
- If review comments can't be resolved (pending after 5 iterations): returns failure
- If git operations fail: surfaces error and STOPS
