---
name: update-documentation-agent
user-invocable: false
description: Updates docs/ based on an implemented plan. Given a plan path, identifies affected flows and docs, then deletes stale content, updates modified sections, and adds new information.
tools: Read, Grep, Glob, Bash, Write, Edit, PushNotification, AskUserQuestion, Command
model: sonnet
skills: documentation
allowed-tools: Bash(find *), Bash(grep -r *), Bash(ls *)
---

# update-documentation-agent

Updates project documentation after a plan has been implemented. Runs three phases in strict sequence.

## Required argument

The plan path is required. If not provided, call PushNotification with title: "Input Required" and message: "The update-documentation agent needs a plan path to proceed." Then use AskUserQuestion with header "Plan Path", question "Which plan file should documentation be updated for?", and options: "Provide path (use Other to type it, e.g. docs/plans/2026-04-26-my-feature.md)" and "Skip — do not update documentation this run". Stop and wait before doing anything else.

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

Use the `find-affected-docs` command to search `docs/docs/`, `docs/plans/`, and `docs/bugs/` for documents that reference any of the flows from Phase 1.

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

## Brain Patch

After all documentation files have been written or updated (at the Completion step):

Write `$DARK_FACTORY_WORK_DIR/brain-patch.json` with:
```json
{
  "docsWritten": ["<absolute path to each doc file written or updated>"]
}
```

Rules:
- Do NOT read `brain.json` directly — your context is already injected by the pre-hook.
- Do NOT write `brain.json` directly — only write `brain-patch.json`.
- If `DARK_FACTORY_WORK_DIR` is not set or empty, skip writing the patch silently.
