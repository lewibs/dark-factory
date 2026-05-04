# pr-agent

**Role**: PR lifecycle manager for completed work.

**Model**: Sonnet (heavy reasoning for PR body composition and comment resolution).

**User-Invocable**: No (invoked by dark-factory-agent after all work is complete).

## Overview

The pr-agent manages the complete PR lifecycle for code that has already been implemented, reviewed, and documented. It opens a PR with a comprehensive body, watches CI until it's green, resolves review comments collaboratively, and stops once CI passes and all threads are resolved. Critically, **the agent does not merge** — it stops at "ready" status, leaving the final merge decision to human judgment.

The PR lifecycle is fully automated except for the final merge decision, enabling code to move from implementation through CI and code review without manual intervention while preserving human control over the merge.

## Input

- `planFilePath` (string, nullable) — Path to the plan file; if null, uses taskDescription
- Or `taskDescription` (string) — Plain description of the work if no plan exists
- If neither: uses git diff

## Orchestration Flow (5 Steps)

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

### Step 2: Open PR

1. **Delegates to create-pr skill** with `bodyFile: "/tmp/pr-body.md"`
2. Receives `prUrl` back from skill
3. **Writes brain-patch.json** in DARK_FACTORY_WORK_DIR:
   ```json
   { "prUrl": "<github PR URL>" }
   ```
   (Skip silently if DARK_FACTORY_WORK_DIR is unset)

### Step 3: Watch CI

1. **Delegates to ci-watch-runner command** with:
   - `prUrl: <the PR URL>`
   - `maxIterations: 5`

2. Command polls PR CI status repeatedly:
   - Checks status at regular intervals
   - Reports when CI is green, yellow (pending), or red (failed)
   - Stops after maxIterations or when status stabilizes

3. **If ciResult.status == "fail"**: returns error, STOPS
   - CI failed; human review of failures required
   - PR remains open for investigation

4. **If ciResult.status == "pass"**: proceeds to Step 4

### Step 4: Resolve Review Comments

1. **Gets PR node ID**:
   - Uses `gh api graphql` to fetch `pr.id` from prUrl

2. **Delegates to comment-resolution-runner command** with:
   - `prUrl: <the PR URL>`
   - `prNodeId: <the PR node ID>`
   - `maxIterations: 5`

3. Command iterates through review comments:
   - Reads each comment thread
   - Attempts to resolve by responding (if automated resolution applies)
   - Or requests human clarification
   - Marks threads resolved when addressed
   - Stops after maxIterations or when all threads are resolved

4. **If commentResult.status == "failed"**: returns error, STOPS
   - Review comments could not be resolved
   - PR remains open with pending threads

5. **If commentResult.status == "success"**: all threads resolved, proceeds to Step 5

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

The PR body includes (from `agents/pr/templates/pr-template.md`):

```markdown
## Summary
- Brief description of changes

## Approach
- How/why this solution was chosen
- Any design decisions

## Test Plan
- [if test suite exists]
- Test output showing all tests passing
- Coverage information if applicable

## Related
- Links to related issues, PRs, or documentation
```

## Key Design Rules

1. **Code is already implemented** — Assume fix is complete; don't re-apply
2. **Always use git -C "$WORK_DIR"** — WORK_DIR is injected by pre-hook
3. **Write body to /tmp/pr-body.md** — Use standard gh cli pattern
4. **Delegate CI watching** — Use ci-watch-runner, don't implement watch loop inline
5. **Delegate comment resolution** — Use comment-resolution-runner, don't implement loop inline
6. **Do NOT merge** — Stop at "ready" status; human makes the merge decision
7. **Write brain-patch after PR opens** — Captures prUrl for downstream use
8. **Skip brain-patch silently if DARK_FACTORY_WORK_DIR unset** — No error

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

This hook performs cleanup specific to PR operations (e.g., removing temporary files, updating metrics).

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
