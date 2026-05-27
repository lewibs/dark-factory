# dark-factory-agent

**Role**: Legacy top-level orchestrator. **DEPRECATED** — use the standalone commands instead.

**Model**: Haiku (lightweight state/routing only, no heavy reasoning).

**User-Invocable**: Yes (via deprecated `/dark-factory:manufacture` command — backward compatibility only).

## Overview

The dark-factory-agent is the legacy entry point for all autonomous feature work, bug debugging, fix flows, and repair operations. It is **deprecated** in favor of five focused standalone commands:

- `/dark-factory:plan` — plan a feature end-to-end (backed by `plan-command-agent`)
- `/dark-factory:execute` — execute an approved plan (backed by `execute-command-agent`)
- `/dark-factory:debug` — debug a non-obvious bug (backed by `debug-command-agent`)
- `/dark-factory:repair` — apply a targeted repair (backed by `repair-command-agent`)
- `/dark-factory:investigate` — investigate a system (backed by `investigation-orchestrator`)

The new standalone commands pass state (planFilePath, prUrl, workDir) directly between steps via local variables rather than writing a `brain.json` file. The `brain-state-manager` skill, pre/post-tool-use hooks, and metrics system (`update-metrics.py`, `metrics.csv`, `/dark-factory:metrics`) have been deleted.

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
- Calls `find-related-pr.sh <taskDescription>` to search for a related open PR
- If a match is found (score ≥ 2 keyword hits against PR title + branch), prompts user via AskUserQuestion:
  - **"Reuse existing branch"** — mounts the existing worktree (or creates one) for the matched branch; sets `USE_EXISTING = true`
  - **"Create new branch"** — proceeds with fresh worktree
- If reusing: derives `existingTaskName` by stripping any `<prefix>/` from the branch name, then sets `WORK_DIR = GIT_ROOT/../<PROJECT_NAME>-<existingTaskName>`; verifies or creates the worktree
- If creating fresh: calls `prep-feature-dir.sh <taskName>` and extracts `WORK_DIR` from script output
- Stops immediately if worktree creation fails (no cleanup needed yet)

### Step 3: Route to Worker Agent
Routes based on classification:
- **"feature"** → `feature-agent` (multi-turn loop: handles planning, question/answer exchanges until `status: "done"`)
  - Handles planning phases, diagram generation, flow approval, and execution
  - May return `status: "question"` requiring user feedback (PushNotification + AskUserQuestion)
  - May return `status: "hard-stop"` (triggers cleanup before halting)
  - Returns `status: "done"` when feature implementation complete
  
- **"fix-flow"** → `fix-flow-orchestrator`
  - Investigates broken flow, generates fix scripts, applies targeted fixes
  
- **"debugger"** → `debugger-agent`
  - Systematic debugging for non-obvious bugs
  
- **"repair"** → `repair-agent`
  - Lightweight, targeted fixes without full plan file

If non-feature worker returns error or hard-stop: runs cleanup, reports error, STOPS

### Step 4: Branch-Drift Guard
- Verifies feature branch has commits ahead of main
- Uses `EXISTING_BRANCH` when reusing a PR, or `feature/<taskName>` for fresh branches
- Bash: `git -C "$WORK_DIR" log main..<branchRef> --oneline`
- Halts with error if no new commits found (cleanup runs first)

### Step 5: Code Review
- Invokes `code-review-orchestrator-agent` with:
  - `planFilePath` (or `"Task: " + taskDescription` if null)
  - `codePath: WORK_DIR`
- Ensures all changes meet review standards
- Halts with cleanup if review fails

### Step 6: Update Documentation
- Invokes `update-documentation-agent` with `planFilePath` and `workDir: WORK_DIR`
- Updates or creates doc files to reflect implemented changes
- Must complete before PR is opened

### Step 7: Harvest Skills (Non-Fatal)
- Tries to invoke `skill-update-agent` with planFilePath, WORK_DIR, taskDescription
- If it fails: logs warning but continues to PR (non-fatal step)
- Extracts reusable patterns for future use

### Step 8: Open Pull Request
- Invokes `pr-agent` with planFilePath (or taskDescription if null)
- Creates PR in the feature worktree
- Halts with cleanup if PR creation fails

### Step 9: Cleanup
- Removes worktree via: `cleanup-worktree.sh WORK_DIR taskName`
- Reports final success with PR URL

## Helper: cleanup(WORK_DIR, taskName)

Called on any error path after worktree creation:
1. Removes worktree via `cleanup-worktree.sh WORK_DIR taskName`

## Key Design Rules

1. **Never write or scaffold code** — All code changes delegate to workers or dependent agents
2. **Always cleanup on error** — Except on prep failure (worktree doesn't exist yet)
3. **Delegate classification logic** — Use task-classifier skill, don't implement inline
4. **Handle null planFilePath** — When worker produces no plan, pass taskDescription as fallback to downstream agents
5. **Never use Explore subagent_type directly** — Always route codebase research through `investigation-agent`; it checks existing docs first (cheap) before scanning the codebase
6. **PR reuse check runs before branch creation** — find-related-pr.sh is invoked at the start of Step 2 so the user can opt into an existing open PR

## Dependencies

- **Skills**: task-classifier
- **Sub-agents**: feature-agent, fix-flow-orchestrator, debugger-agent, repair-agent, code-review-orchestrator-agent, update-documentation-agent, skill-update-agent, pr-agent
- **Scripts**: prep-feature-dir.sh, cleanup-worktree.sh, find-related-pr.sh

## Tools

- Read, Bash, Agent, PushNotification, AskUserQuestion, Skill
