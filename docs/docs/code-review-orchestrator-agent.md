# code-review-orchestrator-agent

**Role**: Orchestrator for automated code review process.

**Model**: Haiku (lightweight orchestration and state management).

**Prompt Caching**: Yes — `cache-control: ephemeral` is set in YAML frontmatter. Claude Code applies prompt caching when spawning this agent, reducing system prompt token costs by ~90% for repeated invocations.

**User-Invocable**: No (invoked by execute-command-agent, debug-command-agent, or repair-command-agent after implementation).

## Overview

The code-review-orchestrator-agent manages the full automated code review workflow. It spawns two parallel reviewers (high-level and low-level), collects their feedback into an issues list, then loops a resolver agent until all issues are resolved. The orchestrator ensures that review cycles are complete before the code proceeds to documentation updates and PR.

## Input

- `planFilePath` (string, required) — Absolute path to the approved plan file (used for context by reviewers)
- `codePath` (string, required) — Directory path or branch name containing the code to review

## Orchestration Flow (6 Steps)

### Step 1: Initialize Issues File

Uses `manage-issues-file` command with `operation: "create"`:
- Creates `<codePath>/issues.md` with empty review points array
- Ready for reviewers to append findings

### Step 2: Spawn Parallel Reviewers

Spawns two reviewers in parallel:

**High-Level Review Agent**:
- Inputs: `planFilePath`, `codePath`
- Checks: architectural decisions, design patterns, code organization, adherence to plan

**Low-Level Review Agent**:
- Input: `codePath`
- Checks: code style, readability, potential bugs, test coverage, performance

Both append their findings to `issues.md` as checklist items.

### Step 3: Wait for Reviewers & Handle Errors

1. Waits for both reviewers to complete
2. If **either reviewer returns an error**:
   - Surfaces the error immediately
   - **Does NOT start the resolver loop**
   - Halts orchestration
3. If **both succeed**:
   - Proceeds to Step 4 (resolver loop)

### Step 4: Resolver Loop

Enters iterative resolution loop:

1. Spawns `resolver-agent` with:
   - `issuesFilePath: <codePath>/issues.md` (absolute path)

2. Waits for resolver to return

3. **If resolver returns an error**:
   - Surfaces error and halts (loop exits)

4. **If resolver returns `anyRemaining: false`**:
   - All issues resolved; exit loop
   - Proceed to Step 5

5. **If resolver returns `anyRemaining: true`**:
   - Issues remain unchecked
   - **Re-enter the loop** (re-spawn resolver)
   - Continue until `anyRemaining: false` or error

**Loop guard**: If resolver loop runs more than **10 iterations** without clearing all items, halt with error describing stuck items.

### Step 5: Delete Issues File

Uses `manage-issues-file` command with `operation: "delete"`:
- Removes `<codePath>/issues.md` (cleanup)
- Confirms successful completion

### Step 6: Return Success

Returns:
```json
{
  "status": "complete"
}
```

## Happy Paths

### orchestrateReview.success
- Both reviewers complete successfully
- Resolver loop runs until `anyRemaining: false`
- All issues resolved
- issues.md deleted

### orchestrateReview.no-issues
- Both reviewers find no issues (empty checklist)
- Resolver sees empty checklist, no-ops
- issues.md deleted immediately
- Returns success

## Error Paths

### orchestrateReview.reviewer-error
- One or both parallel reviewers return an error
- Orchestrator surfaces error without starting resolver
- issues.md may be partially filled

### orchestrateReview.resolver-loop-error
- Resolver returns an error on any iteration
- Orchestrator halts and surfaces the error
- issues.md remains for investigation

### orchestrateReview.resolver-loop-stuck
- Resolver loop runs >10 iterations
- Some items still unchecked
- Orchestrator halts with error describing stuck items

## Key Design Rules

1. **Parallel reviewer spawn** — Both reviewers run simultaneously to save time
2. **Never skip resolver if reviewer fails** — Do not start resolver if either reviewer errored
3. **Loop guard at 10 iterations** — Prevent infinite loops on unresolvable issues
4. **Always delete issues.md on success** — Clean up before returning to caller
5. **Surface all errors** — Never suppress reviewer or resolver errors
6. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase

## Dependencies

- **Commands**: manage-issues-file (create, delete operations)
- **Sub-agents**: high-level-review-agent, low-level-review-agent, resolver-agent

## Tools

- Read, Write, Edit, Bash, Agent, Command

## Return Value

**Success**:
```json
{
  "status": "complete"
}
```

**Error**:
```json
{
  "message": "<error description>"
}
```

## Artifacts

- `<codePath>/issues.md` — Created during review, deleted after resolution
  - Format: markdown checklist of review points
  - Example: `- [ ] Function too long (line 45-67 in main.py)`

## Integration with command agents

1. Called by execute-command-agent, debug-command-agent, or repair-command-agent after the worker agent (feature-agent, debugger-agent, or repair-agent) completes
2. Must complete before update-documentation-agent
3. If returns error: the calling command agent halts, cleans up, reports failure
4. If returns success: the calling command agent continues to documentation and PR
