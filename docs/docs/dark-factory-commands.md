# dark-factory-commands

## Metadata

- System type: `flow`

## System Intent

- What this is: The complete set of user-invocable and internal commands exposed by the dark-factory Claude plugin. Commands are `.md` files in `commands/` that either run bash scripts directly or delegate to a named agent. User-facing commands cover the full manufacture lifecycle (plan, execute, debug, repair), a lightweight save shortcut (save), worktree management, factory terminal management, plugin installation, and documentation investigation. Internal (non-user-invocable) commands are sub-commands called by agents during their own pipelines (ci-watch-runner, comment-resolution-runner, find-affected-docs, manage-issues-file, phase-gate-check, render-plan-section).

## Mermaid Diagram

```mermaid
flowchart TD
  subgraph UserCommands["User-Invocable Commands"]
    PLAN["/dark-factory:plan"]
    EXECUTE["/dark-factory:execute"]
    DEBUG["/dark-factory:debug"]
    REPAIR["/dark-factory:repair"]
    SAVE["/dark-factory:save"]
    GOTOWORKTREE["/dark-factory:goto"]
    INVESTIGATE["/dark-factory:investigation"]
    BUILD["/dark-factory:build-factory"]
    DESTROY["/dark-factory:destroy-factory"]
    INSTALL["/dark-factory:install"]
    GENHOOKS["/dark-factory:gen-hooks"]
  end

  subgraph InternalCommands["Internal Commands (agent-called only)"]
    CIWATCH[ci-watch-runner]
    COMMENTRES[comment-resolution-runner]
    FINDAFFECTED[find-affected-docs]
    MANAGEISSUES[manage-issues-file]
    PHASEGATE[phase-gate-check]
    RENDERPLAN[render-plan-section]
  end

  PLAN --> plan-command-agent
  EXECUTE --> execute-command-agent
  DEBUG --> debug-command-agent
  REPAIR --> repair-command-agent
  SAVE --> pr-agent
  GOTOWORKTREE --> gotoworktree-command-agent
  INVESTIGATE --> investigation-orchestrator

  plan-command-agent --> feature-agent

  execute-command-agent --> execution-agent
  execute-command-agent --> code-review-orchestrator-agent
  execute-command-agent --> update-documentation-agent
  execute-command-agent --> skill-update-agent
  execute-command-agent --> pr-agent

  debug-command-agent --> debugger-agent
  debug-command-agent --> code-review-orchestrator-agent
  debug-command-agent --> update-documentation-agent
  debug-command-agent --> skill-update-agent
  debug-command-agent --> pr-agent

  repair-command-agent --> repair-agent
  repair-command-agent --> code-review-orchestrator-agent
  repair-command-agent --> update-documentation-agent
  repair-command-agent --> skill-update-agent
  repair-command-agent --> pr-agent

  investigation-orchestrator --> investigation-agent
  investigation-orchestrator --> claim-validator-agent

  pr-agent --> CIWATCH
  pr-agent --> COMMENTRES
  COMMENTRES --> CIWATCH
  code-review-orchestrator-agent --> MANAGEISSUES
  update-documentation-agent --> FINDAFFECTED
  feature-agent --> RENDERPLAN
  plan-command-agent --> RENDERPLAN

  BUILD --> build-factory.sh
  DESTROY --> destroy-factory.sh
  INSTALL --> "git pull + claude plugin install"
  GENHOOKS --> gen_hooks.py
```

## Flows

---

### Flow: `plan`

**Command file**: `commands/plan.md`  
**Entry agent**: `agents/dark-factory/agents/plan-command-agent.md`  
**User-invocable**: yes

#### Ordered Steps

1. Derive `taskName` slug from `taskDescription` if not provided.
2. Resolve `PROJECT_DIR` via `git rev-parse --show-toplevel`.
3. Invoke `feature-agent` with `planOnly: true`. This drives the planning phases in a multi-turn loop:
   - **Phase draft_plan**: invoke `planning-agent` (phase=draft_plan), render `## System Intent` via `render-plan-section`, return question to user.
   - **Phase mermaid**: invoke `planning-agent` (phase=mermaid), render `## Mermaid Diagram` via `render-plan-section`, return question to user.
   - **Phase flows**: for each flow, invoke `planning-agent` (phase=flows), render `### Flow: <name>` via `render-plan-section`, return question per flow.
   - **Final approval gate**: show full plan, ask user to "Approve and Execute" or "Abort".
   - When `planOnly: true`, return `{ status: "done", planPath }` instead of invoking `execution-agent`.
   - Repeat loop until `result.status == "done"` or `"aborted"` / `"hard-stop"`.
4. Report: "Plan approved. File: `<planPath>`".

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `plan.success` | taskDescription | planPath | happy path | Plan approved, planPath returned |
| `plan.aborted` | taskDescription | status=aborted message | user abort | User aborted at final approval gate |
| `plan.hard-stop` | taskDescription | status=hard-stop message | error | feature-agent returned hard-stop |

---

### Flow: `execute`

**Command file**: `commands/execute.md`  
**Entry agent**: `agents/dark-factory/agents/execute-command-agent.md`  
**User-invocable**: yes

#### Ordered Steps

1. Validate `planPath` exists on disk; stop if not found.
2. Derive `taskName` from plan file name if not provided (strip date prefix, e.g. `2026-05-27-add-oauth.md` → `add-oauth`).
3. Resolve `PROJECT_DIR` via `git rev-parse --show-toplevel`.
4. Invoke `execution-agent` with `planPath`:
   - Read the plan file.
   - Invoke `skeleton-agent` with `planPath`; assert `tmp/files-checklist.md` is fully checked and all listed files exist.
   - Invoke `testing-agent` with `planPath`; assert `tmp/flows-checklist.md` exists and all new tests are failing.
   - Invoke `implementation-agent` with `planPath` and `tmp/flows-checklist.md`:
     - If returns `hardStop: true`: enter Planning Mode — notify user, ask Resume/Abort; resume by re-spawning `implementation-agent`.
     - If returns `allFlowsGreen: true`: continue.
   - Delete `tmp/files-checklist.md` and `tmp/flows-checklist.md`.
   - Write `brain-patch.json` with artifacts.
   - If user chose Abort during hard-stop: stop with "Execution aborted by user."
5. Invoke `code-review-orchestrator-agent` with `planFilePath` and `codePath` (same pipeline as plan command, steps 4a–4e above).
6. Invoke `update-documentation-agent` with `planFilePath` and `workDir` (same pipeline as plan command).
7. Invoke `skill-update-agent` (non-fatal).
8. Invoke `pr-agent` with `planPath` (same pipeline as plan command).
9. Report: "Execution complete. PR: `<prUrl>`".

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `execute.success` | planPath | prUrl | happy path | All flows green, code-reviewed, docs updated, PR open |
| `execute.plan-not-found` | planPath | error message | error | Plan file does not exist |
| `execute.user-aborted` | planPath | abort message | user abort | User chose Abort during hard-stop |

---

### Flow: `debug`

**Command file**: `commands/debug.md`  
**Entry agent**: `agents/dark-factory/agents/debug-command-agent.md`  
**User-invocable**: yes

#### Ordered Steps

1. Derive `taskName` as `"debug-" + slugify(taskDescription)` if not provided.
2. Resolve `PROJECT_DIR` via `git rev-parse --show-toplevel`.
3. Invoke `debugger-agent` with `taskDescription`:
   - Step 0: invoke `investigation-agent` to understand system context.
   - Confirm bug warrants systematic debugging.
   - Search `docs/bugs/` for matching failure signature; create bug audit log file if not found.
   - Read logs and stack traces.
   - Fill bug file from `bug-audit-log-template`.
   - Write failing reproduction test first.
   - Confirm test fails before fix.
   - Identify root cause from evidence.
   - Apply fix.
   - Confirm test passes.
   - Optionally confirm fix is necessary (remove + re-fail).
   - Record root cause, fix summary, and verification in bug file.
   - Write `brain-patch.json` with `bugFiles` and notes.
4. Set `planFilePath = null` (no plan file for debug route).
5. Invoke `code-review-orchestrator-agent` with `"Task: " + taskDescription` and `codePath` (same pipeline as plan command).
6. Invoke `update-documentation-agent` with `planFilePath=null` and `workDir`.
7. Invoke `skill-update-agent` (non-fatal).
8. Invoke `pr-agent` with `taskDescription` fallback (same pipeline as plan command).
9. Report: "Debug complete. PR: `<prUrl>`".

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `debug.success` | taskDescription | prUrl | happy path | Bug found, fixed, code-reviewed, PR open |
| `debug.agent-error` | taskDescription | error message | error | debugger-agent returned error |

---

### Flow: `repair`

**Command file**: `commands/repair.md`  
**Entry agent**: `agents/dark-factory/agents/repair-command-agent.md`  
**User-invocable**: yes

#### Ordered Steps

1. Derive `taskName` as `"repair-" + slugify(taskDescription)` if not provided.
2. Resolve `PROJECT_DIR` via `git rev-parse --show-toplevel`.
3. Invoke `repair-agent` with `taskDescription`:
   - Step 0: invoke `investigation-agent` to understand system context.
   - Read relevant files; identify minimal change set.
   - Run baseline test suite; record pre-existing failures.
   - Apply the targeted change.
   - Run tests again; iterate up to 5 times fixing new failures only.
   - Return `{ success: true|false, error? }`.
4. If `result.success == false`: report error and stop.
5. Invoke `code-review-orchestrator-agent` with `"Task: " + taskDescription` and `codePath`.
6. Invoke `update-documentation-agent` with `planFilePath=null` and `workDir`.
7. Invoke `skill-update-agent` (non-fatal).
8. Invoke `pr-agent` with `taskDescription`.
   - pr-agent checks for existing PR on current branch via `gh pr view`.
   - If PR exists: commits and pushes to it.
   - If no PR: creates a new one.
9. Report: "Repair complete. PR: `<prUrl>`".

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `repair.success` | taskDescription | prUrl | happy path | Change applied, code-reviewed, PR open (new or existing) |
| `repair.failed` | taskDescription | error message | error | repair-agent returned success=false after 5 iterations |

---

### Flow: `save`

**Command file**: `commands/save.md`  
**Entry agent**: none — delegates directly to `pr-agent`  
**User-invocable**: yes

#### Ordered Steps

1. Resolve `workDir` via `git rev-parse --show-toplevel`.
2. Invoke `pr-agent` with `taskDescription` (defaults to `"Save current changes"` if not provided) and `workDir`.
   - pr-agent handles: commit, push, open/update PR, CI watch, comment resolution.
   - If an existing PR is detected on the branch, it is updated with new commits.
3. If `result.status != "ready"`: stop with `result.reason`.
4. Report: "Saved. PR: `<result.prUrl>`".

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `save.success` | taskDescription (optional) | prUrl | happy path | pr-agent opens PR and returns ready |
| `save.pr-exists` | taskDescription (optional) | prUrl | happy path | Existing PR on branch detected; pr-agent commits and pushes to it |
| `save.pr-agent-error` | taskDescription (optional) | error message | error | pr-agent CI failure or comment resolution failure |

---

### Flow: `goto`

**Command file**: `commands/goto.md`  
**Entry agent**: `agents/dark-factory/agents/gotoworktree-command-agent.md`  
**User-invocable**: yes

#### Ordered Steps

1. Validate that at least one of `prNumber`, `taskName`, or `description` is provided.
2. Resolve `PROJECT_DIR` and `PROJECT_NAME`.
3. Derive `taskName` if not provided:
   - If `prNumber`: look up branch name via `gh pr view`, strip leading `<prefix>/`.
   - If `description`: slugify the description (lowercase, hyphens, ≤30 chars).
4. Search for an existing local worktree at `PROJECT_DIR/../PROJECT_NAME-taskName`.
   - If found: pull `origin main` (or master), report path, stop.
5. Search for an open PR matching `prNumber` or `description` (via `find-related-pr.sh`).
   - If found: extract `EXISTING_BRANCH`, derive `existingTaskName`, set `WORK_DIR`.
     - If worktree does not yet exist: pull main, create worktree via `git worktree add`.
     - Pull `origin main` in worktree, report path, stop.
6. Create new worktree via `prep-feature-dir.sh "$taskName"`.
   - If script fails: report error and stop.
   - Extract `WORK_DIR` from script output.
7. Report: "Worktree ready at: `<WORK_DIR>`". Stop.

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `goto.existing-local` | prNumber/taskName/description | WORK_DIR path | happy path | Existing local worktree found |
| `goto.existing-pr` | prNumber/description | WORK_DIR path | happy path | Open PR branch found; worktree created or reused |
| `goto.new` | taskName/description | WORK_DIR path | happy path | New worktree created via prep-feature-dir.sh |
| `goto.error` | any | error message | error | No input, failed worktree creation |

---

### Flow: `investigation`

**Command file**: `commands/investigation.md`  
**Entry agent**: `agents/commands/investigation-orchestrator.md`  
**User-invocable**: yes

#### Ordered Steps

1. Invoke `investigation-agent` with `system` and optional `question`:
   - Check `docs/docs/` for existing documentation.
   - If docs exist and no corrections: return existing doc path immediately.
   - If docs exist with corrections: update doc to address false claims, return path.
   - If no docs: explore codebase using investigate skill, create `docs/docs/<system-name>.md`.
   - Return file paths written.
2. Capture `docPath` from `investigation-agent` output.
3. Enter validation loop (max 5 iterations):
   - Invoke `claim-validator-agent` with `docPath`:
     - Read doc, extract factual claims (file paths, agent names, command names, behavioral assertions).
     - Verify each claim against source code via `grep -r` and `find`.
     - Return `{ allVerified: boolean, falseClaims: Claim[] }`.
   - If `allVerified == true`: trigger SubagentStop hook (`commit-investigation-docs.sh`) and return `{ docPath, iterations }`.
   - If `falseClaims` exist: format as bullet list with evidence, invoke `investigation-agent` again with `corrections` parameter, update `docPath`, loop.
   - If iterations exceed 5: return error "Max validation iterations exceeded".
4. SubagentStop hook (`commit-investigation-docs.sh`) commits the verified documentation to the repo.

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `investigate.success` | system, question | docPath, iterations | happy path | Doc verified and committed |
| `investigate.doc-exists` | system | docPath | fast path | Doc already in docs/docs/, returned immediately |
| `investigate.max-iterations` | system | error message | error | 5 validation cycles without full verification |

---

### Flow: `build-factory`

**Command file**: `commands/build-factory.md`  
**User-invocable**: yes

#### Ordered Steps

1. Run bash script `${CLAUDE_PLUGIN_ROOT}/scripts/build-factory.sh "${1:-dark factory}"`.
2. Script opens a new terminal window in the current working directory running `claude "/remote-control $NAME"` (where `NAME` defaults to `"dark factory"`). Terminal emulators are tried in priority order: gnome-terminal (GNOME), x-terminal-emulator (Debian/Ubuntu), xterm, konsole (KDE). If none are found, the script exits with an error.

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `build-factory.success` | optional name | new terminal spawned | happy path | |

---

### Flow: `destroy-factory`

**Command file**: `commands/destroy-factory.md`  
**User-invocable**: yes

#### Ordered Steps

1. Run bash script `${CLAUDE_PLUGIN_ROOT}/scripts/destroy-factory.sh "dark factory"`.
2. `destroy-factory.sh` delegates entirely to `close-factory.sh` via `bash "$(dirname "$0")/close-factory.sh"`. `close-factory.sh` does not currently exist in the repo — this is a placeholder/stub with no implemented behavior.

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `destroy-factory.delegated` | optional name | Outcome of close-factory.sh | depends on close-factory.sh | close-factory.sh is missing; script will fail at delegation |

---

### Flow: `install`

**Command file**: `commands/install.md`  
**User-invocable**: yes

#### Ordered Steps

1. `git pull` — pull latest changes.
2. `claude plugin marketplace add "$(pwd)"` — add plugin to marketplace.
3. `claude plugin marketplace update dark-factory` — update marketplace entry.
4. `claude plugin uninstall "dark-factory@dark-factory"` — uninstall old version.
5. `claude plugin install "dark-factory@dark-factory"` — install new version.
6. `bash "${CLAUDE_PLUGIN_ROOT}/scripts/reopen-remote-control.sh" "dark factory"` — reopen remote-control terminal.

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `install.success` | none | Plugin reinstalled | happy path | |

---

### Flow: `gen-hooks`

**Command file**: `commands/gen-hooks.md`  
**User-invocable**: yes

#### Ordered Steps

1. Invoke `scripts/gen_hooks.py` with the current project directory.
2. **scanFrontmatter**: Recursively scan all `.md` files for YAML frontmatter hook declarations (PreToolUse, PostToolUse, Stop, SubagentStop, PreCompact).
3. **mergeIntoSettings**: Merge discovered hooks into `.claude/settings.json` additively; preserve existing entries; deduplicate by command string.
4. Return summary: number of hooks added and duplicates skipped, and path to `.claude/settings.json`.

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `gen-hooks.success` | none | Summary message with hook counts | happy path | |

---

### Flow: `ci-watch-runner` (internal)

**Command file**: `commands/ci-watch-runner.md`  
**User-invocable**: no — called by `pr-agent`

#### Ordered Steps

1. Check if `iterations >= maxIterations`; if so return `{ status: "fail", reason: "Max CI iterations exceeded" }`.
2. Run `gh pr checks <prUrl> --watch` to block until all checks complete or one fails.
3. If all checks have conclusion `SUCCESS`: return `{ status: "pass", checks }`.
4. Collect failing run IDs via `gh pr checks <prUrl> --fail-fast`.
5. For each failing run: spawn `resolve-pr-issue` with `{ type: "ci", runId, failedChecks }`.
   - If `fixResult.skipped == true`: return `{ status: "pass", checks }` (quota exhaustion).
   - If `fixResult.fixed == false`: return `{ status: "fail", reason: ... }`.
   - If fix applied: break inner loop, increment iterations, continue outer loop.

---

### Flow: `comment-resolution-runner` (internal)

**Command file**: `commands/comment-resolution-runner.md`  
**User-invocable**: no — called by `pr-agent`

#### Ordered Steps

1. Check if `iterations >= maxIterations`; if so return `{ status: "failed", reason: "Comment resolution loop exceeded MAX_COMMENT_ITERATIONS" }`.
2. Fetch unresolved review threads via `gh api graphql` using `prNodeId`; filter to `isResolved == false`.
3. If no unresolved threads: return `{ status: "all-resolved", threadsResolved: iterations }`.
4. For each thread: spawn `resolve-pr-issue` with `{ type: "review", threadId, comments }`.
   - If `fixResult.fixed == false`: return `{ status: "failed", reason: ..., threadId }`.
5. After resolving all threads in round: invoke `ci-watch-runner(prUrl, maxIterations=5)`.
   - If CI fails: return `{ status: "failed", reason: "CI failed after resolving threads: ..." }`.
6. Increment iterations, continue loop (check for newly-added threads).

---

### Flow: `find-affected-docs` (internal)

**Command file**: `commands/find-affected-docs.md`  
**User-invocable**: no — called by `update-documentation-agent`

#### Ordered Steps

1. Read `planPath` to extract system names, component names, and key terms.
2. Search `$projectDir/docs/docs/` for `.md` files: match filenames and headers against extracted terms.
3. Search `$projectDir/docs/plans/` for `.md` files: check for same feature (skip current plan).
4. Search `$projectDir/docs/bugs/` for `.md` files: check for related bugs.
5. Return sorted list with match reasons (`{ success: true, affectedDocs: [...], count: N }`).

---

### Flow: `manage-issues-file` (internal)

**Command file**: `commands/manage-issues-file.md`  
**User-invocable**: no — called by `code-review-orchestrator-agent`

#### Operations

- **create**: Initialize `$workDir/issues.md` with review findings array.
- **update**: Mark an issue resolved with resolution details.
- **read**: Return all issues with resolved/total counts.

Note: `code-review-orchestrator-agent` calls `manage-issues-file` with `operation: "delete"` at the end of its review pipeline, but this operation is not defined in `commands/manage-issues-file.md`. The command only defines `create`, `update`, and `read`.

---

### Flow: `phase-gate-check` (internal)

**Command file**: `commands/phase-gate-check.md`  
**User-invocable**: no — called by orchestrators needing explicit phase enforcement

#### Ordered Steps

1. Read `brain.json` from `brainPath`.
2. Mark all phases with `*-complete: true` as completed.
3. Check if `phaseToCheck` has all prerequisites complete.
4. Return `{ canRun: true }` if prerequisites met, else `{ canRun: false, prerequisite, blockingPhases }`.

**Phase dependency order**: `prep` → `worker` → `review` → `docs` → `skills` → `pr` → `cleanup`

---

### Flow: `render-plan-section` (internal)

**Command file**: `commands/render-plan-section.md`  
**User-invocable**: no — called by `feature-agent` and `plan-command-agent`

#### Ordered Steps

1. Read `planPath` from disk.
2. Search for `sectionName` (exact match, line by line).
3. Extract all lines from `sectionName` until the next same-level heading or EOF.
4. Pass extracted content to `${CLAUDE_PLUGIN_ROOT}/scripts/render_section.py`.
5. If render succeeds: return `{ success: true, rendered, fallback: false }`.
6. If render fails: return raw extracted content with `{ fallback: true }`.
7. If section not found: return `{ success: false, reason: "Section not found" }`.

---

## Post-Pipeline Pattern (shared by plan, execute, debug, repair)

All four main manufacture commands share the same post-pipeline after their primary worker agent completes:

```
1. code-review-orchestrator-agent
   └── manage-issues-file (create)
   └── high-level-review-agent (parallel)
   └── low-level-review-agent (parallel)
   └── resolver-agent loop (until anyRemaining=false, max 10)
   └── manage-issues-file (delete) — NOTE: "delete" is not a defined operation in manage-issues-file; this call has no defined behavior

2. update-documentation-agent
   └── find-affected-docs
   └── write/update docs/docs/ files

3. skill-update-agent (non-fatal)
   └── write/update skills/<slug>/SKILL.md files

4. pr-agent
   └── create-pr skill (or push to existing PR)
   └── ci-watch-runner
       └── resolve-pr-issue (per CI failure)
   └── comment-resolution-runner
       └── resolve-pr-issue (per review thread)
       └── ci-watch-runner (after each resolution round)
```

## Logs

| Source | Location |
|--------|----------|
| All commands | Claude Code session output (stdout) |
| brain-patch.json | `$WORK_DIR/brain-patch.json` (ephemeral, written by agents during pipeline) |
| Bug audit logs | `docs/bugs/<yyyy-mm-dd>-<slug>.md` (written by debugger-agent) |
| PR body | `/tmp/pr-body.md` (ephemeral, written by pr-agent) |
| Worktree pointer | `/tmp/dark-factory-work-dir` (ephemeral, absolute path) |
| Metrics | `$projectDir/metrics.csv` (updated by dark-factory-agent on completion) |

## Deployment

- Mechanism: `local only` — Claude Code plugin installed via `claude plugin install`
- Deploy command:
  ```bash
  git pull
  claude plugin marketplace add "$(pwd)"
  claude plugin marketplace update dark-factory
  claude plugin uninstall "dark-factory@dark-factory"
  claude plugin install "dark-factory@dark-factory"
  bash "${CLAUDE_PLUGIN_ROOT}/scripts/reopen-remote-control.sh" "dark factory"
  ```
- Notes: Run from the repo root (`~/github/dark_factory/dark_factory`). The `gen-hooks` command must be run after install to regenerate `.claude/settings.json` hook entries.
