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
  - `"debugger"` — Non-obvious/state-dependent bug
  - `"repair"` — Lightweight targeted change
- If classification is ambiguous: sends PushNotification, awaits AskUserQuestion response

### Step 2: Prep Isolated Work Directory
- Calls `find-related-pr.sh <taskDescription>` to search for a related open PR
- If a match is found (score ≥ 2 keyword hits against PR title + branch), prompts user via AskUserQuestion:
  - **"Reuse existing branch"** — mounts the existing worktree (or creates one) for the matched branch; sets `USE_EXISTING = true`
  - **"Create new branch"** — proceeds with fresh worktree
- If reusing: derives `existingTaskName` by stripping any `<prefix>/` from the branch name, then sets `WORK_DIR = GIT_ROOT/../<PROJECT_NAME>-<existingTaskName>`; verifies or creates the worktree
- If creating fresh: calls `prep-feature-dir.sh <taskName>` and extracts `WORK_DIR` from script output
- Stops immediately if worktree creation fails (no cleanup needed yet)

### Step 3: Create brain.json State File
- Delegates to `brain-state-manager` skill with `operation: "create"`
- Initializes state tracking for the entire task lifecycle
- Stores: taskDescription, taskName, WORK_DIR, PROJECT_DIR, classification
- Stops if brain creation fails

### Step 4: Route to Worker Agent
Routes based on classification:
- **"feature"** → `feature-agent` (multi-turn loop: handles planning, question/answer exchanges until `status: "done"`)
  - Handles planning phases, diagram generation, flow approval, and execution
  - May return `status: "question"` requiring user feedback (PushNotification + AskUserQuestion)
  - May return `status: "hard-stop"` (triggers cleanup before halting)
  - Returns `status: "done"` when feature implementation complete
  
- **"debugger"** → `debugger-agent`
  - Systematic debugging for non-obvious bugs
  
- **"repair"** → `repair-agent`
  - Lightweight, targeted fixes without full plan file

If non-feature worker returns error or hard-stop: runs cleanup, reports error, STOPS

### Step 5: Branch-Drift Guard
- Verifies feature branch has commits ahead of main
- Uses `EXISTING_BRANCH` when reusing a PR, or `feature/<taskName>` for fresh branches
- Bash: `git -C "$WORK_DIR" log main..<branchRef> --oneline`
- Halts with error if no new commits found (cleanup runs first)

### Step 6: Read Plan File Path
- Delegates to `brain-state-manager` with `operation: "read"`
- Extracts `planFilePath` from brain.json (may be null for debugger/repair routes)

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
- Flushes metrics: `python3 update-metrics.py --csv metrics.csv --brain brain.json`
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
9. **PR reuse check runs before branch creation** — find-related-pr.sh is invoked at the start of Step 2 so the user can opt into an existing open PR; the branch-drift guard and all downstream steps are branch-agnostic (use `EXISTING_BRANCH` or `feature/<taskName>` as appropriate)

## Dependencies

- **Skills**: task-classifier, brain-state-manager
- **Sub-agents**: feature-agent, debugger-agent, repair-agent, code-review-orchestrator-agent, update-documentation-agent, skill-update-agent, pr-agent
- **Scripts**: prep-feature-dir.sh, cleanup-worktree.sh, find-related-pr.sh

## Tools

- Read, Bash, Agent, PushNotification, AskUserQuestion, Skill

## State Management

All state persists in `brain.json` within WORK_DIR, managed by brain-state-manager skill:
- Initial creation in Step 3
- Read after feature-agent returns (Step 6)
- Read after pr-agent returns (Step 11)
- Deleted during cleanup (Step 12)
