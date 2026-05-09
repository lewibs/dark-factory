# repair-agent

**Role**: Lightweight, targeted change agent for simple fixes and updates.

**Model**: Haiku (lightweight model; sufficient for targeted, minimal changes).

**User-Invocable**: No (invoked by dark-factory-agent).

## Overview

The repair-agent applies targeted changes from plain-language task descriptions without requiring a full plan file. It is designed for simple, focused fixes: correcting a string, updating a configuration, fixing a broken import, or patching a known issue. The agent runs the test suite, fixes any breakage iteratively (up to 5 attempts), and reports success or failure.

Unlike the debugging agent, repair-agent does not use a systematic debug methodology — it applies a minimal fix and validates it with tests. It is also non-fatal: if repair fails, dark-factory-agent continues to code review and PR instead of halting.

## Input

- `taskDescription` (string) — Plain-language description of what to change or fix (no plan file)

## Workflow (7 Steps)

### Step 0: Resolve WORK_DIR

Before any file operation, repair-agent resolves the working directory from injected brain context:

```
WORK_DIR = $DARK_FACTORY_WORK_DIR (env var)
if WORK_DIR is empty: WORK_DIR = contents of /tmp/dark-factory-work-dir (if the file exists)
if WORK_DIR is still empty: return { success: false, significantChange: false, error: { message: "WORK_DIR could not be resolved from brain context" } }
```

**All file operations (Read/Write/Edit) must use absolute paths prefixed with `$WORK_DIR/`.** CWD-relative paths are forbidden — using them writes files to the main project repo instead of the isolated feature worktree, causing changes to appear as uncommitted modifications on the main branch rather than landing in the PR.

### Step 1: Understand Scope

1. Reads relevant files using absolute `$WORK_DIR/`-prefixed paths
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

### Step 6: Stage Modified Files

Before returning, repair-agent stages all modified files in the feature worktree:

1. Executes `git -C $WORK_DIR add <modified-files>` to stage all changed files
2. Executes `git -C $WORK_DIR status` to verify files are staged

This staging step is required because the SubagentStop hook (`commit-on-subagent-stop.sh`) only commits files that are already staged. Without explicit staging, changes remain unstaged and the hook commits nothing — leaving the repair changes uncommitted in the worktree and absent from the PR branch.

### Step 7: Return Result

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

All modified files are staged via `git -C $WORK_DIR add` before either return path. The SubagentStop hook commits whatever is staged.

## Key Design Rules

1. **Stay minimal** — Do not refactor or clean up code outside the repair scope
2. **No new abstractions** — Don't introduce helpers or patterns not required by the task
3. **All passing tests must remain passing** — Success only when all pre-passing tests still pass (or no suite exists)
4. **Pre-existing failures are noted, not counted** — Only new failures caused by the change block success
5. **5-attempt limit** — Stop iterating after 5 tries; return failure
6. **No plan file required** — This is the lightweight alternative to feature-agent
7. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase
8. **Resolve WORK_DIR at startup** — Always read WORK_DIR from brain context (`$DARK_FACTORY_WORK_DIR` or `/tmp/dark-factory-work-dir` pointer file) before any file operations. Fail fast if WORK_DIR is unresolvable.
9. **Use absolute WORK_DIR paths** — All Read/Write/Edit operations must use `$WORK_DIR/<path>` absolute paths. CWD-relative paths write to the main project repo, not the isolated feature worktree.
10. **Stage all changes before returning** — Execute `git -C $WORK_DIR add <files>` for all modified files. The SubagentStop hook only commits staged changes; unstaged changes are left uncommitted and absent from the PR.

## Dependencies

- **Test runners**: pytest, npm test, go test (auto-detected)
- **Skills**: investigation-delegate (to invoke investigation-agent before applying changes)

## Tools

- Read, Write, Edit, Bash, Glob, Agent, Skill

## Allowed Bash Commands

`Bash(pytest *)`, `Bash(python *)`, `Bash(npm test *)`, `Bash(npm run test *)`, `Bash(go test *)`, `Bash(bash *)`, `Bash(mkdir -p *)`, `Bash(find *)`, `Bash(grep -r *)`, `Bash(aws *)`, `Bash(gh *)`, `Bash(git *)`, `Bash(git -C * add *)`, `Bash(git -C * status *)`

Includes `aws`, `gh`, and `git` so the agent can inspect cloud state, query GitHub, and run git operations when validating cloud-native repairs.

`Bash(git -C * add *)` and `Bash(git -C * status *)` are explicitly allowed for the Step 6 staging requirement — staging all modified files in the feature worktree before the SubagentStop hook fires.

## Error Handling

- If no test suite exists: skips test validation; repair still succeeds if code is syntactically valid
- If repair breaks tests and 5 iterations don't fix it: returns `success: false`
- If target file doesn't exist: reports error and STOPS
- If task description is ambiguous: returns error (repair requires clear, minimal scope)

## SubagentStop Hook

The agent declares a `SubagentStop` hook in its YAML frontmatter:

```yaml
SubagentStop: "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/commit-on-subagent-stop.sh"
```

When the agent finishes, this hook fires and commits all staged changes in the feature worktree with commit message `"fix: repair"`. This ensures repair changes are committed as a discrete step even when the agent is run in non-fatal mode.

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
