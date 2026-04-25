---
name: manage-wiki
description: Use this skill to maintain the plan-first wiki. It defines how plans are structured and linked from the index.
---

## Required

You must use this skill whenever the user asks to update wiki content or create/update plans.

1. Treat plans as the wiki source of truth.
2. Ensure the wiki index points to the plans section.
3. Store new plan content under `docs/plans/`.
4. Register any new wiki page in `mkdocs.yml`.
5. Enforce plan status semantics:
   - `draft`: plan is being created or updated.
   - `approved`: plan is approved but not yet applied in code.
   - `documentation`: code currently exists and matches the plan.
6. Ensure plan contract tables include an `updated` column and mark changed rows with `Y`.
7. Maintain bug documentation under `docs/bugs/` for non-obvious debugging work:
   - Save or update audit logs from `.agent/skills/systematic-debugging/SKILL.md`.
   - Keep one file per unique solved root cause.
   - Do not keep duplicate solved-bug logs.

## Context

### Plan Hierarchy

Use this structure:

- `plan`
- `sub-plan`

Each plan should describe a part of the codebase as a black box at a high level.

The user defines:

- Inputs
- Outputs
- Architecture

The AI helps determine code shape and subparts, unless the user explicitly defines a subplan for a high-importance flow.

## Workflow

1. Check `docs/index.md` and ensure the plans registry is present there.
2. Create or update the target plan in `docs/plans/`.
3. If a plan is edited, set status to `draft` until it is re-approved.
4. Keep plan language high-level and black-box oriented.
5. If a new plan file is added, register it in `mkdocs.yml`.
6. Ensure `docs/index.md` includes a link to `docs/bugs/index.md` and keep `mkdocs.yml` nav aligned when bug pages are added.
