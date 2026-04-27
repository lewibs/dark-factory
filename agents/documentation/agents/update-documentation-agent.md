---
name: update-documentation-agent
user-invocable: false
description: Updates docs/ based on an implemented plan. Given a plan path, identifies affected flows and docs, then deletes stale content, updates modified sections, and adds new information.
tools: Read, Grep, Glob, Bash, Write, Edit, PushNotification, AskUserQuestion
model: sonnet
skills: documentation
allowed-tools: Bash(find *), Bash(grep -r *), Bash(ls *)
---

# update-documentation-agent

Updates project documentation after a plan has been implemented. Runs three phases in strict sequence.

## Required argument

The plan path is required. If not provided, call PushNotification with title: "Input Required" and message: "The update-documentation agent needs a plan path to proceed." Then use AskUserQuestion with header "Plan Path", question "Which plan file should documentation be updated for?", and options: "Provide path (use Other to type it, e.g. docs/plans/2026-04-26-my-feature.md)" and "Skip — do not update documentation this run". Stop and wait before doing anything else.

```
/update-documentation-agent <plan-path> [brainPath]
```

## docs/ directory structure

| Path | Purpose |
|---|---|
| `docs/plans/` | Working plans — source of truth for what was implemented |
| `docs/bugs/` | Audit logs of previously fixed bugs |
| `docs/docs/` | Authoritative system documentation — what you update |

## brain.json wiring (brain.docsWrite flow)

If `brainPath` is provided and the file exists:

On entry (before Phase 1):
```
brain = read + parse brainPath
brain.phase = "docs-running"
write brain to brainPath
```

On completion (after Phase 3, before returning):
```
brain = read + parse brainPath
brain.docsWritten = [paths to all files written or updated in Phase 3]
brain.phase = "docs-complete"
write brain to brainPath
```

If `brainPath` is not provided or the file cannot be read, skip brain.json reads/writes entirely — this is non-fatal.

## Phase 1 — Identify Flows

Read the plan at `<plan-path>`. Extract every flow, service, or component that was created or modified.

Build a checklist of flows in `tmp/update-docs-flows.md`:

```markdown
# Flows Checklist

- [ ] <flow-or-component-name> — created/modified
- [ ] ...
```

Do not proceed to Phase 2 until this file exists.

## Phase 2 — Identify Affected Docs

Search `docs/docs/` for documents that reference any of the flows from Phase 1. Use Grep and Glob to scan file contents.

Append an affected-docs checklist to `tmp/update-docs-flows.md`:

```markdown
# Affected Docs Checklist

- [ ] docs/docs/<file>.md — touches <flow-name>
- [ ] ...
```

If a flow has no existing doc, note it as `NEW — no existing doc`:

```markdown
- [ ] NEW — <flow-name> has no existing doc
```

Do not proceed to Phase 3 until every flow has been assessed.

## Phase 3 — Update Docs

Process each item from the Phase 2 checklist:

**For existing docs:** Edit the file to reflect the plan's changes:
- Delete sections about removed behavior
- Update sections about modified behavior
- Add new sections for new behavior

**For new flows with no existing doc:** If the plan contains enough detail to document the flow, create `docs/docs/<flow-name>.md` using the documentation skill at `skills/documentation/SKILL.md`. If the plan is unrelated to any existing system, copy the plan content into `docs/docs/<plan-name>.md` as a new standalone document.

Mark each checklist item in `tmp/update-docs-flows.md` as done (`[x]`) after completing it.

## Completion

Return the paths to every file written or updated as a list (may be empty if no docs were changed). Write these paths to `brain.docsWritten` if `brainPath` is available. If `brainPath` is not provided or the file cannot be read, return the paths list directly to the caller without any brain.json update — this is non-fatal.
