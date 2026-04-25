---
name: executing-plan
description: Execute plans with a checklist-first workflow, implement and verify all `updated=Y` contract rows, then clear those markers when complete.
---

## Required

Use this skill whenever coding starts from one or more approved plan files.

Follow `.agent/workflows/development-flow.md` for the canonical end-to-end sequence and gates.

1. Confirm preconditions:
   - Plan status is `approved` for new implementation work, or `documentation` when rerunning execution to resolve residual `updated=Y` markers.
   - Stage gates are complete.
   - Planning PR review gate is complete (human approval or merged plan PR).
   - Scope is limited to plans updated in the current commit.
   - Compatibility mode is explicit:
     - `full-replacement` mode: remove dead compatibility code/tests when replaced by the approved contract.
     - `backward-compatible` mode: preserve legacy behavior unless the plan explicitly removes it.
2. Before implementing anything, create a temporary checklist as the core source of truth.
3. Build checklist entries for all plans updated in the current commit and their code targets using this exact format:
   - `[ ] <plan>`
   - `[ ] <plan> -> <file>`
4. Process checklist in order, starting with the first unchecked plan.
5. For each plan, parse high-level flows from its Mermaid diagram to identify required code paths and file targets.
6. Enforce plan contract alignment:
   - Keep behavior aligned with approved Inputs/Outputs, path tables, and approved pseudocode details.
   - Treat any table row with `updated` column value `Y` as required implementation scope.
   - For each flow heading, parse mapped test references:
     - Non-`N/A` references are required test scope and must validate the defined input/output behavior for impacted `updated=Y` rows.
     - `N/A` means no automated test is required for that flow and is an explicit waiver, not a missing mapping.
   - If a flow heading omits test mapping entirely (neither test path nor `N/A`), treat it as plan drift and return to plan update before implementation.
   - Do not change externally visible behavior beyond approved plan contract changes.
7. Implement internals freely as needed for quality (refactors, helper functions, structure changes) as long as plan contracts remain satisfied.
8. After each file update, run the smallest relevant test set for the changed flow/file before marking progress.
9. Treat tests as contract truth during execution:
   - Update code to satisfy tests and approved plan contracts.
   - Do not weaken, delete, or rewrite tests just to make failing code pass.
   - Only change tests when the approved plan contract changed and test updates are required to reflect that new contract.
10. After each file update, check off its `<plan> -> <file>` item only after relevant tests pass for all impacted `updated=Y` rows.
11. When a plan’s file items are complete:
   - Clear the `updated` cell for each path row that was implemented and verified in this execution pass.
   - Confirm no `updated=Y` rows remain in that plan; if any remain, keep working and do not close the plan item.
   - Update Mermaid file-node colors in that plan to show completion with gray (`done/no pending changes`).
   - Update plan `Status` to `documentation` once implementation is complete and verified to match the plan.
   - Check off the plan-level item.
12. Continue iteratively until every checklist item is complete.
13. Delete the temporary checklist file after completion.
14. If implementation drifts from the approved plan at any point:
   - Stop implementation immediately.
   - Notify the developer with the exact mismatch.
   - Return to planning updates first (`reconcile-plans`), then restart execution with a fresh checklist.
15. After implementation is complete, invoke `.agent/skills/code-review/SKILL.md` before shipping:
   - Perform an explicit drift audit first: verify the approved plan contract and the implemented code match in both directions (plan -> code and code -> plan).
   - Review the full execution diff against related plans.
   - Confirm plan-flow test harness coverage and DRY/YAGNI quality gates.
   - Address review findings before considering execution done.
16. After code review findings are resolved, run `.agent/workflows/validate-code.md` to confirm readiness.

## Context

Execution is contract realization, not contract invention.

- Checklist truth: progress is tracked in one temporary checklist file.
- Contract stability: high-level flow contracts are locked to approved plan sections and tables.
- Updated-row priority: rows marked `updated=Y` must be implemented and verified before completion.
- Marker lifecycle: `updated=Y` is a temporary execution marker and must be cleared after verification.
- Test mapping semantics: non-`N/A` flow mappings require executable test coverage; `N/A` is an explicit no-test-required waiver.
- Internal flexibility: implementation details can evolve if external flow contracts hold.
- Drift handling: planning must be updated before coding continues.
- End gate: execution is not complete until `code-review` runs on the implementation diff.
- Final delivery gate: shipping happens only after `code-review` passes.
- Status semantics:
  - `approved` means ready to implement.
  - `documentation` means implementation already matches plan.

## Troubleshooting

- No plans detected in current commit:
  1. Ask the developer which plan(s) to execute.
  2. Do not start coding without plan scope.
- Planning PR review gate not complete:
  1. Stop implementation.
  2. Create/update the planning PR and wait for explicit human approval.
- Plan has Mermaid flows but no matching code targets:
  1. Add missing `<plan> -> <file>` checklist entries.
  2. Implement those files before checking off the plan.
- Plan has `updated=Y` rows but no matching code targets:
  1. Add missing `<plan> -> <file>` checklist entries for each impacted row.
  2. Implement and test those rows before checking off the plan.
- Flow heading has non-`N/A` mapping that does not point to a real test file:
  1. Fix the plan mapping to the correct test file path (or switch to explicit `N/A` if test is intentionally not required).
  2. Do not mark execution complete until mapping is valid.
- Plan has `updated=Y` rows but missing mapped tests:
  1. Add or extend tests to cover each required flow path and I/O behavior.
  2. Do not clear the row marker until tests pass.
- Flow heading omits test mapping entirely:
  1. Return to plan update and add either concrete test path(s) or explicit `N/A`.
  2. Resume execution only after the plan contract is complete.
- Plan status is `documentation` but still has `updated=Y` rows:
  1. Re-run execution verification for the remaining rows.
  2. Clear verified row markers and keep status `documentation` only when no `updated=Y` rows remain.
- Planned behavior needs to change but contract sections are unchanged:
  1. Verify whether plan Inputs/Outputs, path tables (`updated` markers), or Pseudocode were updated.
  2. If not, stop and run `reconcile-plans` first.
- Drift discovered mid-implementation:
  1. Pause immediately and report mismatch.
  2. Update plans and restart with a fresh checklist.
- Tests fail after a file update:
  1. Fix implementation first to satisfy existing tests and approved plan contract.
  2. If failures indicate contract drift, stop and return to `reconcile-plans` before modifying tests.
- Code review finds plan/test/quality gaps after implementation:
  1. Re-open the affected checklist items and fix issues.
  2. Re-run `code-review` before closing execution.
- Lambda import/runtime error appears during local SAM/API execution:
  1. Compare source handler file(s) against `.aws-sam/build/<FunctionName>/app.py` to detect generated-artifact drift.
  2. If drift exists, rebuild SAM artifacts and restart local API.
  3. Re-run the failing flow after rebuild before continuing implementation.
- Full-replacement mode is active but compatibility code remains:
  1. Remove obsolete compatibility code paths and dead tests in the same execution pass.
  2. Ensure plan docs and test mappings reflect only the replacement contract.

## Checklist Format

Use a temp file and keep it current after each file change.

Example:

- [ ] `docs/plans/authentication.md`
- [ ] `docs/plans/authentication.md -> main/server/auth/handler.py`
- [ ] `docs/plans/authentication.md -> main/server/auth/service.py`
