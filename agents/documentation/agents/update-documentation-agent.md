---
name: update-documentation-agent
user-invocable: false
description: Updates docs/ based on an implemented plan. Given a plan path, identifies affected flows and docs, then deletes stale content, updates modified sections, and adds new information.
tools: Read, Grep, Glob, Bash, Write, Edit
model: sonnet
skills: documentation
allowed-tools: Bash(find *), Bash(grep -r *), Bash(ls *)
---

# update-documentation-agent

Updates project documentation after a plan has been implemented. Runs three phases in strict sequence.

## Required argument

The plan path is required. If not provided, before asking the developer for the required plan path, call PushNotification with title: "Input Required" and message: "The update-documentation agent needs a plan path to proceed." Then stop and ask the developer before doing anything else.

```
/update-documentation-agent <plan-path>
```

## docs/ directory structure

| Path | Purpose |
|---|---|
| `docs/plans/` | Working plans — source of truth for what was implemented |
| `docs/bugs/` | Audit logs of previously fixed bugs |
| `docs/docs/` | Authoritative system documentation — what you update |

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

Return the paths to every file written or updated.
