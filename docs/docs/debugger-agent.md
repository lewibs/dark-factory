# debugger-agent

**Role**: Systematic debugger for non-obvious, state-dependent, or intermittent bugs.

**Model**: Sonnet (heavy reasoning for bug investigation and analysis).

**User-Invocable**: No (invoked by debug-command-agent).

## Overview

The debugger-agent runs systematic debugging following a rigorous checklist-based methodology. It is designed for bugs that are non-obvious, state-dependent, intermittent, or of unknown cause — not simple syntax errors or obvious logic bugs. The agent follows the debug skill checklist step-by-step without skipping, producing a bug audit log and a verified fix.

## Input

- `taskDescription` (string) — Description of the bug to debug (what is failing, expected behavior, actual behavior)

## Debugging Workflow (11 Steps)

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

### Step 5: Write Failing Reproduction Test

- Create minimal test case that reproduces the bug
- Arrange inputs per failure conditions
- Assert expected behavior
- Run test on unmodified code to confirm it fails (assertion error, not import/syntax error)
- Verify test fails consistently (not intermittent test failure)
- Note the failure signature in bug file

### Step 6: Understand the System Context

Now that you have a reproducible failure, invoke `investigation-agent` to understand the system context. This ensures you understand the system within the context of a known, reproducible failure (not in the abstract). This approach aligns with "The Art of Debugging" methodology.

Derive the system name from `taskDescription` before invoking so investigation-agent can return cached docs immediately (a cache hit is ~10x faster than a full codebase scan):

```
# Derive system name from taskDescription:
# - Look for agent/component names mentioned (e.g. "debug-command-agent", "pr-agent", "debug skill")
# - Strip filler words ("why is", "the", "so slow", "not working", etc.)
# - Use kebab-case slug (e.g. "debug skill" → "debug", "pr-agent broken" → "pr-agent")
# - Prefer the most specific named component (e.g. "debugger-agent" over "debug")
systemName = extract_system_name(taskDescription)  # e.g. "debug", "pr-agent", "planning"

result = invoke investigation-agent({
  system: systemName,
  question: "<taskDescription>"
})

if result.error:
  log("Investigation failed, proceeding with available knowledge")
else:
  # Use result.content as reference documentation during debugging
  systemDocumentation = result.content
```

### Step 7: Identify Root Cause from Evidence

- Examine code paths involved in failure
- Review logs and stack traces from step 3
- Reference system documentation from step 6
- Form hypothesis about root cause
- Validate hypothesis against all evidence

### Step 8: Fix the Root Problem

- Apply minimal fix targeting identified root cause
- Do not apply workarounds or papering over symptoms
- Do not change unrelated code

### Step 9: Confirm the Test Passes

- Run the reproduction test on fixed code
- Verify it passes consistently
- Document the fix in bug file

### Step 10: Verify Fix is Necessary (when safe)

- Revert fix to unmodified code
- Re-run reproduction test
- Verify it fails as before (confirms fix actually addresses the issue, not coincidence)
- Re-apply fix

### Step 11: Record Root Cause and Verification

Update bug file with:
- **Root Cause**: Explanation of why the bug occurred (reference code locations)
- **Fix Summary**: What was changed and why (reference commit or diff)
- **Verification**: Test name and results confirming the fix

## Brain Patch Output

After all bug files are written and debugging checklist is complete (step 11):

Resolves WORK_DIR (see rule 8) and writes `$WORK_DIR/brain-patch.json`:
```json
{
  "bugFiles": [
    "/absolute/path/to/bug-file-1.md",
    "/absolute/path/to/bug-file-2.md"
  ],
  "notes": [
    "debugger-agent: root cause was <summary>, fixed in <key files>"
  ]
}
```

## Key Design Rules

1. **Follow the checklist in strict order** — Do not skip steps; each step validates the previous one
2. **Read all evidence before coding** — Understand the bug completely before touching code
3. **Write tests before fixing** — Test-first ensures the fix is actually necessary
4. **Understand system in context of failure** — Invoke investigation-agent after a reproducible test is written and confirmed failing, not in the abstract (Step 6). Derive the system name from `taskDescription` before invoking to enable a cache hit; an empty system name always forces a full codebase scan. This ensures system understanding is grounded in a concrete, reproducible failure.
5. **Verify fix is necessary** — Remove fix and confirm test fails again (except when unsafe)
6. **Do NOT read brain.json** — Context is already injected by pre-hook
7. **Do NOT write brain.json directly** — Only write brain-patch.json
8. **Resolve WORK_DIR via pointer file fallback** — Use `$DARK_FACTORY_WORK_DIR` if set; else read contents of `/tmp/dark-factory-work-dir`; skip brain-patch silently if both are empty
9. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase

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
