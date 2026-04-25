---
name: update-plan
description: Update an existing plan in docs/plans by restarting the stage-gated new-plan workflow from Stage 1. Use when a user asks to revise an existing @plan (small edit or major restructure), including explicit stage gate reset and fresh approvals.
---

## Required

Use this skill whenever an existing plan needs to be changed.

1. Resolve the target plan file in `docs/plans/`.
2. Read the current plan and summarize current contract boundaries before editing.
3. Reset the target plan's Stage Gate Tracker to unchecked:
   - `[ ] Stage 1 Mermaid approved`
   - `[ ] Stage 2 I/O contracts approved`
   - `[ ] Stage 3 pseudocode approved or skipped`
4. Immediately set plan `Status` to `draft` when any plan content is updated.
5. Keep existing metadata unless the user explicitly asks to change:
   - `Plan type`
   - `Parent plan`
   - `Depends on` (or legacy `Depandency plans`)
   - `Status`
6. Run the same staged workflow used by `.agent/skills/new-plan/SKILL.md` in strict order:
   - Stage 1: Mermaid diagram updates
     - For cross-plan boundaries, use plan-file references (`docs/plans/*.md`) instead of internal implementation files in the other subsystem.
   - Stage 2: Black-box I/O contract updates
     - If a contract is owned by another plan, point to that plan as source-of-truth and avoid redefining internals here.
   - Stage 3: Acceptance criteria and plan-first tests
   - Stage 4: Pseudocode (optional)
   - Every `### Flow` heading must include either concrete test file path(s) or explicit `N/A` when no automated test is required.
   - Every contract table must include an `updated` column; set `Y` for rows changed in the current revision.
7. Require explicit user approval before moving from one stage to the next.
8. Support both change sizes without bias:
   - Small, localized contract update
   - Large restructuring/re-scoping rewrite
9. When stages are complete and approved, mark the Stage Gate Tracker as checked and set final status according to user direction:
   - `approved`: approved but not yet applied in code.
   - `documentation`: code currently exists and matches the updated plan contract.
10. After finishing the target plan, run `.agent/skills/reconcile-plans/SKILL.md` to propagate ripple updates to linked plans.
11. Before any implementation begins, require a planning PR and human review gate:
   - Create a PR for the updated plan/reconciliation diff.
   - Wait for explicit human approval (or merge) before invoking `.agent/skills/executing-plan/SKILL.md`.

## Context

Treat `update-plan` as a contract re-negotiation workflow for existing plans.

- Do not patch sections ad hoc without stage flow.
- The reset is mandatory even for small edits.
- Updated plans are always `draft` until re-approved.
- Updated plan must remain black-box focused.
- Test intent must track revised contracts.
- Human plan-review PR gate is mandatory before implementation starts.

## Troubleshooting

- Target plan is ambiguous:
  1. Ask the user to confirm the exact plan path in `docs/plans/`.
- User asks to skip stage approvals:
  1. Follow user instruction if explicitly requested.
  2. Document that approvals were user-skipped in plan notes or tracker context.
- User requests metadata changes mid-flow:
  1. Apply metadata change immediately.
  2. Continue at the active stage.
- Edits affect linked plans:
  1. Finish target plan first.
  2. Then run `reconcile-plans`.
