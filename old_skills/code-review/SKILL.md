---
name: code-review
description: Review code changes against plan contracts, test-harness flow coverage, and engineering quality standards (including DRY and YAGNI). Use when reviewing a PR, diff, or code changes for correctness and readiness.
---

# Code Review

Use this skill only for review tasks (not implementation).

## Steps

1. Identify review scope:
   - List changed files and the behaviors they affect.
   - Locate related plan files in `docs/plans/` that define those behaviors.
2. Verify plan contract alignment (required):
   - Check whether code behavior matches documented Inputs/Outputs and flow paths.
   - Flag any plan drift where behavior changed but plan contract did not.
   - If no applicable plan exists for changed behavior, flag as a review finding.
3. Verify test harness coverage against plan flows (required):
   - For each relevant plan flow, confirm there is an automated test path or explicit `N/A` waiver in plan docs.
   - Validate that tests cover happy path, error path, and key edge paths called out by the plan.
   - Flag missing, weak, or non-deterministic tests as findings.
4. Review code quality and maintainability (required):
   - Enforce DRY: avoid duplicated logic without a clear reason.
   - Enforce YAGNI: avoid speculative abstractions/features not required by current plan/contract.
   - Check readability, naming, error handling, and obvious correctness/performance risks.
5. Report findings in severity order with exact references:
   - `Critical`, `Major`, `Minor`, `Nitpick`.
   - Include `path:line` and concrete impact.
   - Keep summary brief and place it after findings.

## Context

Code review is a contract-validation pass, not style-only commentary.

- Plans are source-of-truth for intended behavior.
- Tests are source-of-truth for executable verification.
- DRY and YAGNI prevent entropy and over-engineering.

## Troubleshooting

- Plan exists but flows are unclear:
  1. Flag ambiguity and request a plan update before approving behavior changes.
- Code changes without matching tests:
  1. Mark as incomplete and specify which flow-path tests are missing.
- Tests pass but behavior contradicts plan:
  1. Treat as plan drift and require either code rollback or plan reconciliation.

## Template

Use `templates/code-review-checklist.md` as the default review scaffold.
