---
name: reconcile-plans
description: Iteratively update all impacted plans by walking plan metadata (parent and dependency plans) with a temporary checklist until every discovered plan is reviewed and up to date.
---

## Required

Use this skill whenever a plan is created or changed and linked plans may need updates.

Follow `.agent/workflows/development-flow.md` for the canonical end-to-end sequence and gates.

1. Start from plan metadata in each plan file (from `new-plan/templates/plan-template.md`):
   - `Plan type`
   - `Parent plan`
   - `Depends on` (accept legacy `Depandency plans` if present)
2. Create a temporary checklist file before making ripple updates.
3. Seed the checklist with the changed plan(s).
4. Process plans iteratively until the checklist has no pending items.
5. For each plan processed, recursively discover related plans in this order:
   - Parent plan first
   - Then dependency plans
6. For each discovered plan:
   - If not already in checklist, add it as pending review.
   - Review whether contract updates are required.
   - If updates are required, update the plan and keep traversal going from that plan.
   - If updates are required, set the updated plan `Status` to `draft` while editing.
   - Ensure all plan contract tables include an `updated` column; set `Y` on changed rows.
   - If no updates are required, mark as reviewed/no-change.
7. For each updated plan, set Mermaid node colors using this change-state scheme:
   - Gray: unchanged
   - Yellow: updated
   - Red: deleted
   - Green: new
8. After each plan is handled, mark its checklist status (`updated` or `no-change`).
9. Continue until all checklist items are checked off and no new plans are added.
10. When complete, delete the temporary checklist file.
11. Preserve contract-level language; do not add implementation details.
12. For each edited plan, finalize `Status` by meaning:
   - `approved`: plan approved but code not yet applied.
   - `documentation`: code already exists and matches the plan.
13. After reconciliation updates are complete, create a planning PR for human review before any implementation:
   - Open a PR containing plan/reconciliation changes using `.agent/skills/create-pull-request/SKILL.md`.
   - Request explicit human validation that plan contracts are sound and not speculative.
14. Only after human plan review is approved (or merged), move to `.agent/skills/execute-plan/SKILL.md` for implementation.

## Context

Treat plan updates as graph reconciliation, not one-file edits.

- One plan change can cascade through parent/dependency edges.
- Use metadata-driven traversal to avoid missing ripple updates.
- Keep a single source of truth in the checklist while iterating.
- Stop only when every discovered plan is reviewed.
- Mermaid color state makes pending/updated/new/deleted impact visible.
- Human review gate is mandatory between planning and implementation.

## Troubleshooting

- Metadata field naming varies:
  1. Accept `Depends on`, `Depandency plans`, and `Dependency plans`.
  2. Normalize links before enqueueing.
- Recursive loops or repeated links:
  1. Do not re-add items already present in checklist.
  2. Mark duplicates as already-reviewed and continue.
- Unsure whether to edit a discovered plan:
  1. Prefer explicit review and mark `no-change` with rationale.
  2. Do not skip discovered plans silently.
- Checklist grows during updates:
  1. This is expected; continue iterative processing.
  2. Finish only when no pending rows remain.
- Mermaid colors are inconsistent:
  1. Reapply the four-state scheme (gray/yellow/red/green).
  2. Ensure colors reflect the actual final plan diff.
- Human reviewer requests plan changes:
  1. Return to the affected plan(s), update contracts, and re-run reconciliation.
  2. Re-open or update the planning PR and wait for approval again before execution.

## Checklist Format

Create a temp file (for example with `mktemp`) and track all review work there.

Example rows:

| status | plan-path | discovered-from | action |
| --- | --- | --- | --- |
| `pending` | `<docs/plans/a.md>` | `seed` | `review` |
| `pending` | `<docs/plans/b.md>` | `<docs/plans/a.md>` | `review` |
| `updated` | `<docs/plans/a.md>` | `seed` | `edited` |
| `no-change` | `<docs/plans/b.md>` | `<docs/plans/a.md>` | `reviewed` |

Delete this temp checklist file after all rows are resolved.

## Next Skill

Once this skill is complete and human plan review is approved, use `.agent/skills/execute-plan/SKILL.md`.
