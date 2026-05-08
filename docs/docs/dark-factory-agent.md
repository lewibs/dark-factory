# dark-factory-agent

**Role**: Top-level dark-factory orchestrator and entry point for all manufacturing tasks.

**Model**: Haiku (lightweight state/routing only, no heavy reasoning).

**User-Invocable**: Yes (primary command-line entry point).

## Overview

The dark-factory-agent is the single entry point for all autonomous feature work, bug debugging, fix flows, and repair operations. It orchestrates an entire unit of work end-to-end: classifying the task, isolating work in a fresh directory, delegating to the appropriate worker agent, reviewing results, keeping documentation current, opening a PR, and cleaning up.

The agent never writes or modifies code itself — it delegates entirely to specialized workers based on task classification.

## Input

- `taskDescription` — Verbatim user request (what to build, fix, or investigate)
- `taskName` (optional) — Short slug for the work directory (e.g. `add-oauth`, `fix-login-bug`). If not provided, derived from taskDescription (lowercase, hyphens, ≤30 chars)

## Orchestration Flow (12 Steps)

### Step 1: Classify Task
- Delegates to `task-classifier` skill
- Skill determines if task is:
  - `"feature"` — New feature or enhancement
  - `"fix-flow"` — Known-broken integration flow
  - `"debugger"` — Non-obvious/state-dependent bug
  - `"repair"` — Lightweight targeted change
- If classification is ambiguous: sends PushNotification, awaits AskUserQuestion response

### Step 2: Prep Isolated Work Directory
- Resolves `PLUGIN_ROOT` at runtime from `~/.claude/plugins/installed_plugins.json` using explicit plugin name lookup (`d['plugins'].get('dark-factory@dark-factory')`). `${CLAUDE_PLUGIN_ROOT}` is only available in hook command environments, NOT in Bash tool call subprocesses — using it here would produce an empty string and path failure.
- If `PLUGIN_ROOT` is empty: reports error and STOPS immediately
- Calls bash: `"$PLUGIN_ROOT/agents/dark-factory/scripts/prep-feature-dir.sh" <taskName>`
- Creates isolated git worktree for the task
- Stops immediately if worktree creation fails (no cleanup needed yet)
- Extracts `WORK_DIR` from script output

### Step 3: Create brain.json State File
- Delegates to `brain-state-manager` skill with `operation: "create"`
- Initializes state tracking for the entire task lifecycle
- Stores: taskDescription, taskName, WORK_DIR, PROJECT_DIR, classification
- Stops if brain creation fails

### Step 4: Route to Worker Agent
Routes based on classification:
- **"feature"** → `feature-agent` (single invocation)
  - feature-agent runs at depth 2 and calls AskUserQuestion directly for all user interaction.
  - dark-factory-agent invokes feature-agent ONCE and waits for a terminal status:
    - `status: "done"` → feature work complete, continue to Step 5
    - `status: "hard-stop"` → cleanup, report reason, STOP
    - `status: "aborted"` → cleanup, report "User aborted", STOP
    - Any other status → cleanup, report unexpected status, STOP
  - There is NO multi-turn loop — feature-agent handles all user approvals internally via AskUserQuestion.
  - Never falls through to sub-planning-agent or any other agent if feature-agent returns unexpected output.
  
- **"fix-flow"** → `fix-flow-orchestrator`
  - Investigates broken flow, generates fix scripts, applies targeted fixes
  
- **"debugger"** → `debugger-orchestrator` (3-agent pattern: orchestrator, reproduce-test-agent, debugger-fix-agent)
  - Systematic debugging for non-obvious bugs
  
- **"repair"** → `repair-agent`
  - Lightweight, targeted fixes without full plan file

If non-feature worker returns error or hard-stop: runs cleanup, reports error, STOPS

### Step 5: Branch-Drift Guard
- Verifies feature branch has commits ahead of main
- Bash: `git -C "$WORK_DIR" log main..feature/<taskName> --oneline`
- Halts with error if no new commits found (cleanup runs first)

### Step 6: Read Plan File Path and Validate Brain State
- Delegates to `brain-state-manager` with `operation: "read"`
- Extracts `planFilePath` from brain.json (may be null for debugger/repair routes)
- **Validation**: If `planFilePath` is null AND classification is "feature", logs warning:
  - feature-agent always writes planFilePath on success, so null indicates brain-patch.json write failure
  - Warning alerts developer before proceeding to downstream agents with degraded context

### Step 7: Code Review
- Invokes `code-review-orchestrator-agent` with:
  - `planFilePath` (or `"Task: " + taskDescription` if null)
  - `codePath: WORK_DIR`
- Ensures all changes meet review standards
- Halts with cleanup if review fails

### Step 8: Update Documentation
- Invokes `update-documentation-agent` with `planFilePath` and `workDir: WORK_DIR`
- Passing `workDir` ensures the agent writes doc files into the isolated worktree, not the main repo
- Updates or creates doc files to reflect implemented changes
- Must complete before PR is opened

### Step 9: Harvest Skills (Non-Fatal)
- Tries to invoke `skill-update-agent` with planFilePath, WORK_DIR, taskDescription
- If it fails: logs warning but continues to PR (non-fatal step)
- Extracts reusable patterns for future use

### Step 10: Open Pull Request
- Invokes `pr-agent` with planFilePath (or taskDescription if null)
- Creates PR in the feature worktree
- Halts with cleanup if PR creation fails

### Step 11: Read PR Metadata
- Delegates to `brain-state-manager` with `operation: "read"`
- Extracts `prUrl` and `projectDir` from brain.json for final report

### Step 12: Metrics & Cleanup
- Flushes metrics into `$WORK_DIR/metrics.csv` (the feature branch worktree): `python3 update-metrics.py --csv $WORK_DIR/metrics.csv --brain brain.json`
- Commits and pushes metrics.csv to the feature branch so it lands in the PR: `git -C $WORK_DIR add metrics.csv && git -C $WORK_DIR commit -m 'chore: update metrics.csv' && git -C $WORK_DIR push`
- Copies metrics.csv back to `$projectDir/metrics.csv` so the local main copy stays current before the PR is merged
- Deletes brain.json via brain-state-manager
- Removes worktree via: `cleanup-worktree.sh WORK_DIR taskName`
- Reports final success with PR URL

## Helper: cleanup(WORK_DIR, taskName)

Called on any error path after worktree creation:
1. Deletes brain.json via `brain-state-manager({ operation: "delete", workDir: WORK_DIR })`
2. Removes worktree via `cleanup-worktree.sh WORK_DIR taskName`

## Key Design Rules

1. **Never write or scaffold code** — All code changes delegate to workers or dependent agents
2. **Always cleanup on error** — Except on prep failure (worktree doesn't exist yet)
3. **Delegate classification logic** — Use task-classifier skill, don't implement inline
4. **Delegate brain.json management** — Use brain-state-manager skill, never write brain.json directly
5. **Handle null planFilePath** — When worker produces no plan, pass taskDescription as fallback to downstream agents
6. **Read brain state after sub-agents** — Use brain-state-manager to extract outputs, don't parse agent return values directly
7. **Rely on pre-hook injection** — The pre-hook injects brain context into every Agent tool call automatically; don't manually pass brain fields
8. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase
9. **Steps 7-9 are mandatory** — Code review, docs, and skills steps must always execute to completion; never skip regardless of user input or override phrases
10. **FORBIDDEN: Direct brain.json writes** — Never write brain.json via cat, echo, Bash, or any tool; always use brain-state-manager skill
11. **FORBIDDEN: Direct sub-planning-agent invocation** — Always route through feature-agent; if feature-agent returns non-JSON output, report error and stop
12. **FORBIDDEN: Never merge a PR manually** — pr-agent returns `status: ready` but does not merge. Never instruct any sub-agent to merge. Merging is the developer's responsibility after human review.
13. **Worktree lifecycle is owned by dark-factory-agent** — Sub-agents (including pr-agent) must NOT declare SubagentStop hooks that delete brain.json or remove the worktree. A SubagentStop hook on a sub-agent fires before dark-factory-agent regains control, destroying brain.json before Steps 11-12 can read prUrl and flush metrics. Cleanup runs exclusively in Step 12 (success path) and the cleanup() helper (error paths).

## Dependencies

- **Skills**: task-classifier, brain-state-manager
- **Sub-agents**: feature-agent, fix-flow-orchestrator, debugger-orchestrator (+ reproduce-test-agent, debugger-fix-agent), repair-agent, code-review-orchestrator-agent, update-documentation-agent, skill-update-agent, pr-agent
- **Scripts**: prep-feature-dir.sh, cleanup-worktree.sh

## Tools

- Read, Bash, Agent, PushNotification, AskUserQuestion, Skill

## State Management

All state persists in `brain.json` within WORK_DIR, managed by brain-state-manager skill:
- Initial creation in Step 3
- Read after feature-agent returns (Step 6)
- Read after pr-agent returns (Step 11)
- Deleted during cleanup (Step 12)
