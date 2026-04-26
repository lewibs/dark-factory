# Agents

## Overview

The `agents/` directory contains all orchestration logic for Dark Factory. Agents are markdown files with YAML front-matter that Claude Code loads as sub-agents. Each agent has a narrowly-scoped responsibility and delegates all writing/editing to other agents or skills.

## Agent Inventory

### dark-factory (top-level orchestrator)

**File:** `agents/dark-factory/agents/dark-factory-agent.md`

The root orchestrator invoked by `/dark-factory:manufacture`. It:

1. Runs `agents/dark-factory/scripts/prep-feature-dir.sh <taskName>` to create an isolated working directory (`dark_factory-<taskName>/`).
2. Classifies the task and routes to the correct worker:
   - New feature → `feature-agent`
   - Broken integration / end-to-end failure → `fix-flow-orchestrator`
   - Bug / crash / unexpected behavior → `debugger-agent`
3. Runs `code-review-orchestrator-agent` on the result.
4. Runs `update-documentation-agent` (must complete before the PR step).
5. Runs `skill-update-agent` (non-fatal — failure only logs a warning).
6. Invokes `pr-agent` to open, CI-watch, resolve comments, and merge.
7. Cleans up the isolated work directory.

The agent never writes, edits, or scaffolds code itself — it delegates entirely.

**Classification rules:**

| Signal | Worker |
|---|---|
| "add", "build", "create", "implement", "new feature" | `feature-agent` |
| "broken flow", "integration failing", "end-to-end", "pipeline" | `fix-flow-orchestrator` |
| "bug", "crash", "error", "fix", "broken", "not working", "debug" | `debugger-agent` |
| Ambiguous | Sends a PushNotification, then asks a single clarifying question |

---

### featurework

**Directory:** `agents/featurework/`

Handles end-to-end feature implementation through three layers:

- **`feature-agent`** (`agents/featurework/agents/feature-agent.md`) — orchestrates planning → approval gate → execution. Invokes `planning-agent`, presents the plan to the developer, loops on feedback, then invokes `execution-agent` after approval. Sends a PushNotification before requesting approval. Never opens a PR itself.
- **`planning-agent`** (`agents/featurework/planning/agents/planning-agent.md`) — reads the codebase and writes a plan file under `docs/plans/`.
- **`execution-agent`** (`agents/featurework/execution/agents/execution-agent.md`) — implements the approved plan. Has sub-agents: `implementation-agent`, `skeleton-agent`, `testing-agent`.

---

### debugger

**File:** `agents/debugger/agents/debugger-agent.md`

Runs systematic debugging on non-obvious, state-dependent, or intermittent bugs. Steps:

1. Confirms the bug warrants systematic debugging.
2. Creates or reuses a `docs/bugs/<yyyy-mm-dd>-<bug-slug>.md` audit log.
3. Reads all relevant logs and stack traces before touching code.
4. Follows the debug checklist: write failing test → confirm failure → identify root cause → fix → confirm pass → optionally revert and re-confirm failure.
5. Records root cause, fix summary, and verification in the bug file.

---

### fix-flow

**Directory:** `agents/fix-flow/`

Autonomously drives a failing integration flow to green. Three phases:

1. **Phase 1 — Understand System**: spawns `investigation-agent` to document the named flow, writes `docs/plans/system-diagram.md`.
2. **Phase 2 — Setup**: spawns `setup-wizard` to generate trigger/fetch-logs/wait-for-completion/deploy scripts.
3. **Phase 3 — Fix and Push**: spawns `ralph-fix-and-push` which loops: trigger → debug → PR → deploy until the flow passes.

---

### code-review

**Directory:** `agents/code-review/`

Orchestrates automated code review. Entry point: `code-review-orchestrator-agent`.

1. Creates `tmp/issues.md`.
2. Spawns `high-level-review-agent` and `low-level-review-agent` in parallel.
3. Enters a resolver loop: spawns `resolver-agent` repeatedly until `anyRemaining` is false (max 10 iterations).
4. Deletes `tmp/issues.md` and returns `{ status: "complete" }`.

---

### documentation

**Directory:** `agents/documentation/`

Three agents handle documentation lifecycle:

- **`investigation-agent`** — explores the codebase for a named system, validates or creates `docs/docs/<system-name>.md`. Uses `skills/investigate`, `skills/documentation`, and `skills/detect-drift`.
- **`update-documentation-agent`** — after a plan is implemented, identifies affected flows, locates relevant `docs/docs/` files, and updates or creates them in three phases (identify flows → identify affected docs → update docs). Requires a plan path; sends PushNotification if missing.
- **`detect-drift-agent`** — audits parity between `docs/` and the actual implementation.

---

### initialization

**Directory:** `agents/initialization/`

- **`init-orchestrator-agent`** — entry point for `/dark-factory:init`. Runs `agents/initialization/scripts/init.sh`, sets `bypassPermissions` in `~/.claude/settings.json`, invokes `init-docs-agent`, and opens an "init: dark factory" PR via `pr-agent`.
- **`init-docs-agent`** — discovers major systems in the project, invokes `investigation-agent` for each, writes `docs/docs/` files, `docs/docs/README.md`, and `CLAUDE.md`.

---

### pr

**Directory:** `agents/pr/`

- **`pr-agent`** — stages all changes (`git add --all`), writes PR body from `agents/pr/templates/pr-template.md` to `/tmp/pr-body.md`, opens PR, waits for CI, spawns `resolve-pr-issue` for failures or unresolved review threads, squash-merges, deletes the branch, and returns `{ pr_url, merged: true }`.
- **`resolve-pr-issue`** — resolves a single CI failure or review thread.

---

### skill-update

**File:** `agents/skill-update/agents/skill-update-agent.md`

After a manufacture run completes, reviews the completed work (plan file + git diff), identifies non-obvious patterns likely to recur, and writes or updates `skills/<slug>/SKILL.md` files. Returns `{ skillsWritten: [] }` when no qualifying patterns are found. Never modifies agent files or files outside `skills/`.

## Front-matter conventions

Every agent file has a YAML front-matter block:

| Field | Purpose |
|---|---|
| `name` | Agent identifier |
| `user-invocable` | Whether the agent can be invoked directly by the developer |
| `description` | One-line summary |
| `tools` | Comma-separated list of Claude tools the agent may use |
| `model` | Model to use (typically `sonnet`) |
| `skills` | Skill files the agent references |
| `allowed-tools` | Fine-grained bash command allowlist |
| `scripts` | Shell scripts the agent is permitted to run |

Agents that call `PushNotification` in their body must declare it in `tools:` — the Claude Code runtime silently skips notifications for agents missing this declaration (see `docs/bugs/`).
