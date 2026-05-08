# Debugger Flow Architecture

**Classification**: debugger (systematic bug fixing via test-first workflow)

**Model**: Haiku orchestrator + Sonnet workers

**User-Invocable**: No (invoked by dark-factory-agent when classification="debugger")

## Overview

The debugger flow is a 3-agent orchestrator pattern that coordinates systematic debugging of non-obvious, state-dependent, or intermittent bugs. Each agent is responsible for a distinct phase and commits its work independently via SubagentStop hooks.

The three agents are:
1. **debugger-orchestrator** (haiku) — Entry point; coordinates triage, investigation, and sub-agent sequencing
2. **reproduce-test-agent** (sonnet) — Writes failing reproduction test and commits with "test: <slug> (red)"
3. **debugger-fix-agent** (sonnet) — Applies fix, verifies causality, and commits with "fix: <slug>"

## Architecture

```
debugger-orchestrator
├── Step 0: investigation-agent (understand system context)
├── Step 1: Triage (confirm bug is non-obvious)
├── Step 2: Create bug audit log file (docs/bugs/<date>-<slug>.md)
├── Step 3: Read all evidence (logs, stack traces)
├── Step 4: Fill bug audit log template
├── Step 5: invoke reproduce-test-agent ──→ [red commit: "test: <slug> (red)"]
├── Step 6: invoke debugger-fix-agent ──→ [green commit: "fix: <slug>"]
└── Step 7: Write brain-patch.json
```

## Input

- `taskDescription` (string) — Description of the bug to debug (failure signature, expected vs actual behavior)

## Commit Sequence

The orchestration produces **two deterministic commits**:

1. **Red commit** (reproduce-test-agent SubagentStop): `"test: <bug-slug> (red)"`
   - Stages: reproduction test file(s) only
   - Triggers after reproduce-test-agent confirms test fails on unmodified code

2. **Green commit** (debugger-fix-agent SubagentStop): `"fix: <bug-slug>"`
   - Stages: source code fix file(s) + updated bug audit log
   - Triggers after debugger-fix-agent verifies test passes with fix applied

## Workflow Steps

### Step 0: Understand System Context

Debugger-orchestrator invokes investigation-agent to gather authoritative documentation about the system components involved in the failure. This ensures accurate diagnosis before debugging begins.

**If investigation succeeds**: Use documented system context during analysis
**If investigation fails**: Proceed with available knowledge

### Step 1: Triage

Confirm the bug warrants systematic debugging:
- Bug is non-obvious (root cause not immediately clear)
- OR bug is state-dependent, intermittent, or requires understanding system interactions

If the bug is trivial/obvious (simple typo, obvious logic error):
- Report and STOP
- Suggest using repair-agent for simple fixes

### Step 2: Find or Create Bug File

Search `docs/bugs/` for existing audit log matching the failure signature.

**If found**: Use existing file (append new findings)
**If not found**: Create `docs/bugs/<YYYY-MM-DD>-<bug-slug>.md`
- Date: Today's date
- Slug: Hyphenated short identifier for the bug
- Example: `docs/bugs/2026-05-08-parser-eof-crash.md`

Write the bug slug to `/tmp/dark-factory-bug-slug` for sub-agent access.

### Step 3: Read All Relevant Evidence

**Critical rule**: Do not modify code until evidence is fully understood.

1. Read all relevant logs, stack traces, and error messages
2. Examine reproduction steps and failure conditions
3. Identify test runs that exhibit the failure
4. Gather system state snapshots if applicable
5. Review system documentation from Step 0

### Step 4: Fill Bug Audit Log Template

Document findings in the bug file using bug-audit-log-template:

- **Failure Signature**: Exact error or failure mode observed
- **Reproduction Steps**: Steps to reliably trigger the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: System, OS, versions
- **Relevant Logs**: Stack traces, error messages
- **Hypotheses**: Theories about root cause based on evidence (not yet confirmed)

Commit this initial state: `git -C $WORK_DIR add docs/bugs/* && git -C $WORK_DIR commit -m "docs: initial bug audit log"`

### Step 5: invoke reproduce-test-agent

Debugger-orchestrator spawns reproduce-test-agent with:
- `bugFilePath` — Absolute path to bug audit log
- `bugSlug` — Bug slug extracted from filename (for commit message)
- `workDir` — Absolute path to feature worktree

**reproduce-test-agent responsibilities**:
1. Write a minimal failing reproduction test
   - Unit test preferred (fast, isolated)
   - Can be integration test if needed
   - Place in appropriate directory (tests/, test/, spec/, etc.)
   - Include clear comment about the bug it reproduces

2. Run and confirm test fails
   - Execute appropriate test runner: `pytest`, `npm test`, `python -m unittest`, etc.
   - Confirm test **fails with assertion error** (not syntax/import error)
   - Log failure output for debugging reference

3. Stage test file(s) only
   - Execute: `git -C $WORK_DIR add <test-files>`
   - Verify: `git -C $WORK_DIR diff --cached` shows only test additions

4. SubagentStop hook fires
   - Hook reads `/tmp/dark-factory-bug-slug` to get bug slug
   - Hook commits: `git -C $WORK_DIR commit -m "test: <bug-slug> (red)"`
   - Agent execution ends

### Step 6: invoke debugger-fix-agent

Debugger-orchestrator spawns debugger-fix-agent with:
- `bugFilePath` — Absolute path to bug audit log
- `bugSlug` — Bug slug (for commit message)
- `workDir` — Absolute path to feature worktree

**debugger-fix-agent responsibilities**:
1. Identify root cause from evidence
   - Review evidence already in bug file
   - Review reproduction test created by reproduce-test-agent
   - Trace execution path to identify root cause
   - Validate hypothesis against all evidence

2. Apply minimal fix
   - Apply only the minimal change needed to fix root problem
   - NO workarounds, hacks, or defensive patterns
   - Target the actual root cause, not symptoms
   - Keep changes focused and small

3. Verify causality (mandatory)
   - Run reproduction test: should now **PASS**
   - Verify test failure → fix removal → test failure again (confirms fix is necessary)
   - Re-apply fix and confirm test passes
   - Document verification in bug file

4. Update bug audit log
   - Add root cause summary and code location references
   - Document fix applied and files modified
   - Record verification steps completed
   - Mark test status as "PASSING"

5. Stage fixed files
   - Execute: `git -C $WORK_DIR add <fix-files> docs/bugs/*`
   - Stage source code files that were modified
   - Also stage the updated bug audit log
   - Verify: `git -C $WORK_DIR diff --cached` shows only fixes and bug log updates

6. SubagentStop hook fires
   - Hook reads `/tmp/dark-factory-bug-slug` to get bug slug
   - Hook commits: `git -C $WORK_DIR commit -m "fix: <bug-slug>"`
   - Agent execution ends

### Step 7: Write brain-patch.json

After both sub-agents complete, debugger-orchestrator writes the final state:

Resolves WORK_DIR:
```
WORK_DIR = $DARK_FACTORY_WORK_DIR
if WORK_DIR empty: WORK_DIR = contents of /tmp/dark-factory-work-dir
if WORK_DIR still empty: skip silently
```

Writes `$WORK_DIR/brain-patch.json`:
```json
{
  "bugFiles": [
    "/absolute/path/to/docs/bugs/<date>-<slug>.md"
  ],
  "notes": [
    "debugger-orchestrator: Completed 3-agent refactoring flow: reproduce → fix → verify"
  ]
}
```

## Key Design Rules

1. **Strict phase sequencing**: Reproduce → Fix → Verify (enforced by orchestrator)
2. **Read all evidence before coding** — Understand bug completely before touching code
3. **Write tests before fixing** — Test-first ensures fix is actually necessary
4. **Minimal, focused fixes** — Target root cause only, no defensive patterns
5. **Verify causality** — Remove fix and confirm test fails again (confirms necessity)
6. **SubagentStop commits** — Each sub-agent commits its own work independently
7. **No direct brain.json access** — Use brain-patch.json only
8. **WORK_DIR via pointer file** — Orchestrator writes `/tmp/dark-factory-bug-slug` and `/tmp/dark-factory-work-dir` for sub-agents
9. **Never use Explore directly** — Route codebase research through investigation-agent

## Dependencies

- **Skills**: investigation-delegate (for orchestrator's investigation-agent call)
- **Templates**: bug-audit-log-template (for bug file structure)
- **Sub-agents**: reproduce-test-agent, debugger-fix-agent
- **Hooks**: commit-on-subagent-stop.sh (for sub-agent commits)

## Tools

**Orchestrator (debugger-orchestrator)**:
- Read, Write, Agent, Bash, Skill
- Model: haiku

**Test Writer (reproduce-test-agent)**:
- Read, Bash, Glob
- Model: sonnet
- Allowed: `Bash(bash *)`, `Bash(pytest *)`, `Bash(npm test *)`, `Bash(python *)`, `Bash(grep -r *)`, `Bash(find *)`

**Fixer (debugger-fix-agent)**:
- Read, Edit, Bash, Glob
- Model: sonnet
- Allowed: `Bash(bash *)`, `Bash(pytest *)`, `Bash(npm test *)`, `Bash(python *)`, `Bash(grep -r *)`, `Bash(find *)`, `Bash(git -C * add *)`, `Bash(git -C * commit *)`

## Artifacts Produced

On the feature branch, the orchestration produces:

1. **Reproduction test file(s)** — Committed in red commit by reproduce-test-agent
2. **Source code fix file(s)** — Committed in green commit by debugger-fix-agent
3. **Bug audit log** — `docs/bugs/<YYYY-MM-DD>-<bug-slug>.md` — Committed with green commit (updated by debugger-fix-agent)
4. **Brain patch** — `$DARK_FACTORY_WORK_DIR/brain-patch.json` — State metadata for dark-factory-agent (not committed)

## Error Handling

- **Bug too simple**: Triage reports and stops (suggest repair-agent)
- **Cannot write test**: Report blocker and stop
- **Cannot identify root cause**: Document findings and report inconclusive
- **Cannot apply fix**: Document blocker and stop

## SubagentStop Hooks

Both sub-agents declare SubagentStop hooks in their YAML frontmatter:

```yaml
SubagentStop: "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/commit-on-subagent-stop.sh"
```

**reproduce-test-agent SubagentStop**: Commits red test with message `"test: <bug-slug> (red)"`

**debugger-fix-agent SubagentStop**: Commits green fix with message `"fix: <bug-slug>"`

Both hooks read `/tmp/dark-factory-bug-slug` to construct the dynamic commit message.

## Commit Message Format

- Red commit: `test: <bug-slug> (red)` — signals test is failing before fix
- Green commit: `fix: <bug-slug>` — signals bug is fixed and test passes

The `<bug-slug>` is extracted from the bug filename (everything after the date prefix).
Example: For file `2026-05-08-parser-eof-crash.md`, slug is `parser-eof-crash`.
