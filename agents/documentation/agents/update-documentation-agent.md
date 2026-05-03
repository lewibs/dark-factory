---
name: update-documentation-agent
user-invocable: false
description: Updates docs/ based on an implemented plan. Given a plan path, identifies affected flows and docs, then deletes stale content, updates modified sections, and adds new information.
tools: Read, Bash, Write, Edit, PushNotification, AskUserQuestion, Command
model: sonnet
skills: documentation
commands: find-affected-docs
allowed-tools: Bash(find *), Bash(ls *)
---

# update-documentation-agent

Updates project documentation after a plan has been implemented.

## Required argument

If no plan path is provided: PushNotification("Input Required", "update-documentation-agent needs a plan path."), then AskUserQuestion for the path or skip option.

## Phase 1 — Identify Flows

Read the plan at `<plan-path>`. Extract every flow, service, or component that was created or modified.

Build `tmp/update-docs-flows.md`:
```markdown
# Flows Checklist
- [ ] <flow-name> — created/modified
```

## Phase 2 — Identify Affected Docs

Invoke find-affected-docs command with the flow names from Phase 1.

Append to `tmp/update-docs-flows.md`:
```markdown
# Affected Docs Checklist
- [ ] docs/docs/<file>.md — touches <flow-name>
- [ ] NEW — <flow-name> has no existing doc
```

## Phase 3 — Update Docs

For each item in the Phase 2 checklist:

- **Existing doc**: edit to reflect plan changes — delete removed behavior, update modified, add new.
- **New flow**: create `docs/docs/<flow-name>.md` using the documentation skill.

Mark each checklist item `[x]` when done.

## Completion

Write `$DARK_FACTORY_WORK_DIR/brain-patch.json`:
```json
{ "docsWritten": ["<absolute path to each file written or updated>"] }
```
Skip silently if DARK_FACTORY_WORK_DIR is unset.
