# debugger-agent

**Role**: Systematic debugger for non-obvious, state-dependent, or intermittent bugs.

**Model**: Sonnet (heavy reasoning for bug investigation and analysis).

**User-Invocable**: No (invoked by dark-factory-agent).

## Overview

The debugger-agent runs systematic debugging following a rigorous checklist-based methodology. It is designed for bugs that are non-obvious, state-dependent, intermittent, or of unknown cause — not simple syntax errors or obvious logic bugs. The agent follows the debug skill checklist step-by-step without skipping, producing a bug audit log, two deterministic commits (red and green test states), and a verified fix.

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

1. **5.1: Write a failing reproduction test**
   - Minimal test case that reproduces the bug
   - Arrange inputs per failure conditions
   - Assert expected behavior
   - Confirm test fails (assertion error, not import/syntax error)

2. **5.2: Confirm the test fails before any fix**
   - Run test on unmodified code
   - Verify it fails consistently (not intermittent test failure)
   - Note the failure signature in bug file
   - **After confirming failure, make the red commit**: stage only the test file(s) and commit with message `"test: <bug-slug> (red)"`

3. **5.3: Identify root cause from evidence**
   - Examine code paths involved in failure
   - Review logs and stack traces from step 3
   - Form hypothesis about root cause
   - Validate hypothesis against all evidence

4. **5.4: Fix the root problem**
   - Apply minimal fix targeting identified root cause
   - Do not apply workarounds or papering over symptoms
   - Do not change unrelated code

5. **5.5: Confirm the test passes**
   - Run the reproduction test on fixed code
   - Verify it passes consistently
   - Document the fix in bug file
   - **After confirming pass, make the green commit**: stage only the fix file(s) and commit with message `"fix: <bug-slug>"`

6. **5.6: Remove the fix and confirm it fails again** (when safe)
   - Revert fix to unmodified code
   - Re-run reproduction test
   - Verify it fails as before (confirms fix actually addresses the issue, not coincidence)
   - Re-apply fix

### Step 6: Record Root Cause and Verification

Update bug file with:
- **Root Cause**: Explanation of why the bug occurred (reference code locations)
- **Fix Summary**: What was changed and why (reference commits)
- **Verification**: Test name and results confirming the fix

## Commit Sequence

The debugger-agent produces three deterministic commits to the feature branch:

1. **Red commit** (after step 5.2): `"test: <bug-slug> (red)"` — stages only the reproduction test file(s)
2. **Green commit** (after step 5.5): `"fix: <bug-slug>"` — stages only the fix file(s)
3. **Docs commit** (SubagentStop hook, after checklist): `"docs: add bug audit log"` — stages the bug audit log and any supporting documentation

This sequence clearly shows the test-first discipline and the minimal scope of each fix.

## Brain Patch Output

After all bug files are written and debugging checklist is complete:

Resolves WORK_DIR (see rule 7) and writes `$WORK_DIR/brain-patch.json`:
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
4. **Make red and green commits** — Commit the test after step 5.2 (before fix) and the fix after step 5.5 (after test passes)
5. **Verify fix is necessary** — Remove fix and confirm test fails again (except when unsafe)
6. **Do NOT read brain.json** — Context is already injected by pre-hook
7. **Do NOT write brain.json directly** — Only write brain-patch.json
8. **Resolve WORK_DIR via pointer file fallback** — Use `$DARK_FACTORY_WORK_DIR` if set; else read contents of `/tmp/dark-factory-work-dir`; skip brain-patch silently if both are empty
9. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase

## Dependencies

- **Skills**: systematic-debugging (contains debug checklist)
- **Templates**: bug-audit-log-template

## Tools

- Read, Write, Bash, Glob, Agent, Skill

## Allowed Bash Commands

`Bash(bash *)`, `Bash(pytest *)`, `Bash(python *)`, `Bash(npm test *)`, `Bash(grep -r *)`, `Bash(find *)`, `Bash(aws *)`, `Bash(gh *)`, `Bash(docker *)`, `Bash(curl *)`

Includes cloud-native tooling (`aws`, `gh`, `docker`, `curl`) so the agent can fetch remote logs, query cloud resources, and inspect container state without silently failing on cloud-hosted projects.

## Error Handling

- If bug is obviously simple (not non-obvious/state-dependent): report and STOP
- If test cannot be written: report blocker and STOP
- If root cause cannot be identified after evidence review: document findings in bug file and report inconclusive
- If fix cannot be applied: document blocker and STOP

## SubagentStop Hook

The agent declares a `SubagentStop` hook in its YAML frontmatter:

```yaml
SubagentStop: "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/commit-on-subagent-stop.sh"
```

When the agent finishes (after step 5.6 and root cause documentation), this hook fires and commits all staged changes in the feature worktree with commit message `"docs: add bug audit log"`. This is the third and final commit in the sequence, after the red and green commits created in steps 5.2 and 5.5.

## Artifacts Produced

The debugger-agent produces the following artifacts on the feature branch:

1. **Test file(s)** — Reproduction test(s) for the bug (committed in red commit)
2. **Fix file(s)** — Fixed source code (committed in green commit)
3. **Bug audit log** — `docs/bugs/<yyyy-mm-dd>-<bug-slug>.md` — Full documentation of the bug, root cause, fix, and verification (committed in docs commit via SubagentStop hook)
4. **Brain patch** — `$DARK_FACTORY_WORK_DIR/brain-patch.json` — Metadata linking to bug files (consumed by dark-factory-agent, not committed directly)

The three commits in order are:
- `test: <bug-slug> (red)` — test file(s) only
- `fix: <bug-slug>` — source fix file(s) only
- `docs: add bug audit log` — bug audit log and supporting docs
