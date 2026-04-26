# Skills

## Overview

The `skills/` directory contains reusable skill files that agents reference during execution. Skills are markdown documents (`SKILL.md`) that describe a concrete, repeatable procedure. They are not agents — they do not have their own invocation lifecycle. An agent reads a skill file and follows its steps.

There are two categories of skills:

1. **Project-level skills** (`skills/`) — general-purpose skills applicable to any project using Dark Factory.
2. **Agent-local skills** (`agents/<agent-name>/skills/`) — skills scoped to a specific agent's workflows.

## Project-Level Skills

### install

**File:** `skills/install/SKILL.md`

Instructions for installing or updating the Dark Factory plugin in Claude Code via `claude plugin marketplace add` and `claude plugin install dark-factory`.

---

### install-plugin

**File:** `skills/install-plugin/SKILL.md`

Instructions for installing a Claude Code plugin from a local path.

---

### logging

**File:** `skills/logging/SKILL.md`

Instruments code flows with structured log statements. Log format: `log<flow><step><data>`. Steps:

1. Accept a path to a plan, bug, or doc file.
2. Extract every flow and write a checklist to `tmp/logging-checklist.md` using `skills/logging/templates/logging-checklist-template.md`.
3. Add a log at each meaningful step (entry, branch, error, exit) in the implementation file.
4. Delete `tmp/logging-checklist.md` after all flows are instrumented.

Does not introduce new dependencies — uses the project's existing logger (`console.log`, `logger.info`, Python `logging`, etc.).

---

### create-mermaid-diagram

**File:** `skills/create-mermaid-diagram/SKILL.md`

Produces a Mermaid diagram from a codebase or plan. Used to visualize flows.

---

### find-dead-code

**File:** `skills/find-dead-code/SKILL.md`

Scans the codebase for dead code: exported symbols with no callers, unreachable branches, and unused imports.

---

### declare-tools-in-agent-frontmatter

**File:** `skills/declare-tools-in-agent-frontmatter/SKILL.md`

Procedure for ensuring all tools called in an agent body are also declared in its YAML front-matter `tools:` field, preventing silent runtime failures.

---

### handle-idempotent-setup-script

**File:** `skills/handle-idempotent-setup-script/SKILL.md`

Pattern for writing setup scripts that are safe to run more than once (idempotent). Guards against re-creating directories or resources that already exist.

---

### open-in-vscode

**File:** `skills/open-in-vscode/SKILL.md`

Opens a file or directory in VS Code from within an agent context.

## Agent-Local Skills

Agent-local skills live under `agents/<agent-name>/skills/` and are referenced in the agent's front-matter `skills:` field.

### documentation (agents/documentation/skills/)

| Skill | File | Purpose |
|---|---|---|
| `investigate` | `skills/investigate/SKILL.md` | Explore an unknown codebase — entry points, data flow, log sources, failure modes, deployment discovery |
| `documentation` | `skills/documentation/SKILL.md` | Write or update a `docs/docs/` file using the documentation template |
| `detect-drift` | `skills/detect-drift/SKILL.md` | Audit parity between `docs/plans/` or `docs/docs/` and actual implementation |

### debugger (agents/debugger/skills/)

| Skill | File | Purpose |
|---|---|---|
| `debug` | `skills/debug/SKILL.md` | Step-by-step systematic debugging checklist with bug audit log template |

### fix-flow (agents/fix-flow/skills/)

| Skill | File | Purpose |
|---|---|---|
| `generate-fetch-logs` | `skills/generate-fetch-logs/SKILL.md` | Generates a script to fetch logs from a running integration flow |
| `generate-wait-for-completion` | `skills/generate-wait-for-completion/SKILL.md` | Generates a polling script that waits for a flow to complete |
| `generate-trigger` | `skills/generate-trigger/SKILL.md` | Generates a script to trigger an integration flow |
| `generate-deploy` | `skills/generate-deploy/SKILL.md` | Generates a deploy script for a flow |

### pr (agents/pr/skills/)

| Skill | File | Purpose |
|---|---|---|
| `create-pr` | `skills/create-pr/SKILL.md` | Scripts and procedures for opening, watching, and merging a GitHub PR via `gh` |

## Skill File Format

```
---
name: <slug>
description: "<one sentence: what this skill does and when to use it>"
user-invocable: false
---
## When to use
<condition>

## Steps
<numbered steps>

## Notes
<caveats or gotchas>
```

Skills written by `skill-update-agent` follow this template exactly. Existing skills are merged (never overwritten) when the agent identifies the same pattern recurs.
