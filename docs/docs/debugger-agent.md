# debugger-agent

**Role**: Systematic debugger for non-obvious, state-dependent, or intermittent bugs.

**Model**: Sonnet (heavy reasoning for bug investigation and analysis).

**User-Invocable**: No (invoked by dark-factory-agent).

## Overview

The debugger-agent runs systematic debugging following a rigorous checklist-based methodology. It is designed for bugs that are non-obvious, state-dependent, intermittent, or of unknown cause — not simple syntax errors or obvious logic bugs. The agent follows the debug skill checklist step-by-step without skipping, producing a bug audit log and a verified fix.

## Input

- `taskDescription` (string) — Description of the bug to debug (what is failing, expected behavior, actual behavior)

## Debugging Workflow (6 Steps)

### Step 1: Confirm Bug Warrants Systematic Debugging

Verify the bug is:
- Non-obvious (root cause not immediately clear)
- State-dependent (behavior depends on system state, timing, or conditions)
- Intermittent (fails inconsistently)
- Unknown cause (not obviously a typo or simple logic error)

If the bug is obviously simple, report it and STOP (use repair-agent instead for simple fixes).

### Step 2: Search for Existing Bug File

1. Searches `docs/bugs/` for an existing file with the same failure signature
2. If found: uses existing file, appends findings
3. If not found: creates `docs/bugs/<yyyy-mm-dd>-<bug-slug>.md` (dated, hyphenated slug of bug description)

### Step 3: Read All Relevant Evidence Before Touching Code

**Critical rule**: Do not modify code until evidence is understood.

1. Reads all relevant logs, stack traces, and error messages
2. Examines reproduction steps and failure conditions
3. Identifies all test runs that exhibit the failure
4. Gathers system state snapshots if applicable

### Step 4: Fill Bug Audit Log

Uses `bug-audit-log-template` to document:
- **Failure Signature**: Exact error or failure mode observed
- **Reproduction Steps**: Steps to reliably trigger the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: System, OS, Python/Node version, etc.
- **Relevant Logs**: Stack traces, error messages, logs from failing runs
- **Hypotheses**: Theories about root cause based on evidence (not yet confirmed)

### Step 5: Run Debugging Checklist

Follows this sequence in strict order:

1. **Write a failing reproduction test**
   - Minimal test case that reproduces the bug
   - Arrange inputs per failure conditions
   - Assert expected behavior
   - Confirm test fails (assertion error, not import/syntax error)

2. **Confirm the test fails before any fix**
   - Run test on unmodified code
   - Verify it fails consistently (not intermittent test failure)
   - Note the failure signature in bug file

3. **Identify root cause from evidence**
   - Examine code paths involved in failure
   - Review logs and stack traces from step 3
   - Form hypothesis about root cause
   - Validate hypothesis against all evidence

4. **Fix the root problem**
   - Apply minimal fix targeting identified root cause
   - Do not apply workarounds or papering over symptoms
   - Do not change unrelated code

5. **Confirm the test passes**
   - Run the reproduction test on fixed code
   - Verify it passes consistently
   - Document the fix in bug file

6. **Remove the fix and confirm it fails again** (when safe)
   - Revert fix to unmodified code
   - Re-run reproduction test
   - Verify it fails as before (confirms fix actually addresses the issue, not coincidence)
   - Re-apply fix

### Step 6: Record Root Cause and Verification

Update bug file with:
- **Root Cause**: Explanation of why the bug occurred (reference code locations)
- **Fix Summary**: What was changed and why (reference commit or diff)
- **Verification**: Test name and results confirming the fix

## Brain Patch Output

After all bug files are written and debugging checklist is complete:

Writes `$DARK_FACTORY_WORK_DIR/brain-patch.json`:
```json
{
  "bugFiles": [
    "/absolute/path/to/bug-file-1.md",
    "/absolute/path/to/bug-file-2.md"
  ]
}
```

## Key Design Rules

1. **Follow the checklist in strict order** — Do not skip steps; each step validates the previous one
2. **Read all evidence before coding** — Understand the bug completely before touching code
3. **Write tests before fixing** — Test-first ensures the fix is actually necessary
4. **Verify fix is necessary** — Remove fix and confirm test fails again (except when unsafe)
5. **Do NOT read brain.json** — Context is already injected by pre-hook
6. **Do NOT write brain.json directly** — Only write brain-patch.json
7. **Skip brain-patch silently if DARK_FACTORY_WORK_DIR unset** — No error if environment variable missing

## Dependencies

- **Skills**: systematic-debugging (contains debug checklist)
- **Templates**: bug-audit-log-template

## Tools

- Read, Write, Edit, Bash, Glob, Agent

## Error Handling

- If bug is obviously simple (not non-obvious/state-dependent): report and STOP
- If test cannot be written: report blocker and STOP
- If root cause cannot be identified after evidence review: document findings in bug file and report inconclusive
- If fix cannot be applied: document blocker and STOP

## Artifacts Produced

- `docs/bugs/<yyyy-mm-dd>-<bug-slug>.md` — Bug audit log (persisted in repository)
- `$DARK_FACTORY_WORK_DIR/brain-patch.json` — Metadata linking to bug files
