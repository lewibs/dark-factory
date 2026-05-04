# repair-agent

**Role**: Lightweight, targeted change agent for simple fixes and updates.

**Model**: Sonnet (heavy reasoning for targeted problem-solving).

**User-Invocable**: No (invoked by dark-factory-agent).

## Overview

The repair-agent applies targeted changes from plain-language task descriptions without requiring a full plan file. It is designed for simple, focused fixes: correcting a string, updating a configuration, fixing a broken import, or patching a known issue. The agent runs the test suite, fixes any breakage iteratively (up to 5 attempts), and reports success or failure.

Unlike the debugging agent, repair-agent does not use a systematic debug methodology — it applies a minimal fix and validates it with tests. It is also non-fatal: if repair fails, dark-factory-agent continues to code review and PR instead of halting.

## Input

- `taskDescription` (string) — Plain-language description of what to change or fix (no plan file)

## Workflow (6 Steps)

### Step 1: Understand Scope

1. Reads relevant files based on task description
2. Identifies the minimal set of files that need to change
3. **Does NOT refactor or expand scope** beyond what is asked
4. Determines: "What is the smallest change that satisfies this request?"

### Step 2: Run Baseline Tests

1. Detects test runner by checking for:
   - `pytest` (Python)
   - `npm test` or `npm run test` (Node.js)
   - `go test` (Go)
   - Other common runners

2. If no test suite found: **skips to Step 4** (no tests to validate)

3. If test suite found: runs full suite once
   - Records which tests are **already failing** (pre-existing)
   - These failures are NOT counted against the repair

### Step 3: Apply Targeted Change

1. Makes the minimal change described in taskDescription
2. Focuses modifications on identified files
3. Keeps changes tight and focused (no refactoring)
4. Does not introduce new abstractions, helpers, or patterns outside the task scope

### Step 4: Assess Significance

Sets `significantChange` flag based on whether any modified file is:

**Significant if changed**:
- Agent instruction file (`*.md` inside `agents/`)
- Skill definition (`SKILL.md`)
- User-facing command (inside `commands/`)
- Public API or interface boundary

**Not significant otherwise**:
- Data files
- Configuration files
- Comments-only changes
- Internal implementation details

### Step 5: Fix Failures

1. Runs test suite again
2. Identifies **new failures** (not in pre-existing baseline)
3. **Iterative loop** (up to 5 attempts):
   - If new failures found:
     - Diagnose the failure
     - Apply a targeted fix
     - Re-run test suite
     - Check for new failures
   - If no new failures: proceed to Step 6

4. **After 5 attempts**: if new test failures still exist:
   - Returns `{ success: false, significantChange, error: { message: "<last failure summary>" } }`
   - Notes pre-existing failures but doesn't count them

### Step 6: Return Result

**Success**:
```json
{
  "success": true,
  "significantChange": true|false
}
```

**Failure**:
```json
{
  "success": false,
  "significantChange": true|false,
  "error": {
    "message": "<summary of last test failure>"
  }
}
```

## Key Design Rules

1. **Stay minimal** — Do not refactor or clean up code outside the repair scope
2. **No new abstractions** — Don't introduce helpers or patterns not required by the task
3. **All passing tests must remain passing** — Success only when all pre-passing tests still pass (or no suite exists)
4. **Pre-existing failures are noted, not counted** — Only new failures caused by the change block success
5. **5-attempt limit** — Stop iterating after 5 tries; return failure
6. **No plan file required** — This is the lightweight alternative to feature-agent

## Dependencies

- **Test runners**: pytest, npm test, go test (auto-detected)
- **No skills or sub-agents required**

## Tools

- Read, Write, Edit, Bash, Glob

## Error Handling

- If no test suite exists: skips test validation; repair still succeeds if code is syntactically valid
- If repair breaks tests and 5 iterations don't fix it: returns `success: false`
- If target file doesn't exist: reports error and STOPS
- If task description is ambiguous: returns error (repair requires clear, minimal scope)

## Lifecycle in dark-factory-agent

1. Invoked by dark-factory-agent as non-fatal step
2. If returns `success: false`: logged but dark-factory-agent continues to code review and PR
3. If returns `success: true`: continues to code review
4. No brain-patch.json written (repair-agent produces no artifacts for downstream use)

## Use Cases

- Fix a typo or string constant
- Update a configuration value
- Correct a broken import
- Patch a known one-liner issue
- Update a version pin
- Fix a small bug with clear solution
