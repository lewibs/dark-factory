---
name: detect-drift
description: Audit plan-to-code parity across all docs/plans files. Use when validating ship readiness, reconciling plan drift, or checking whether documented flows/files/tests match implemented code and whether major implemented flows are missing from docs.
---

## Required

Use this skill whenever plan drift may exist, especially during `.agent/workflows/validate-code.md`.

1. Build plan inventory and baseline checklist artifacts.
   - Read `docs/index.md` (fallback to `docs/plans/index.md` only for legacy repos).
   - Enumerate all plan docs in `docs/plans/*.md`.
   - Flag catalog drift (listed-but-missing, unlisted-but-present).
   - Generate checklists before auditing:
     - `.venv/bin/python .agent/skills/detect-drift/scripts/generate_checklists.py`
   - Review:
     - `docs/plans/checklists/DRIFT-SUMMARY.md`
     - `docs/plans/checklists/plans/*.md`
     - `docs/plans/checklists/ui-surfaces/*.md`
   - Temporary artifact rule:
     - Files under `docs/plans/checklists/` are process-only temporary artifacts.
     - Do not keep generated checklist files after reporting findings to the user.
2. Validate plan references and flow targets (docs -> code).
   - For each plan, inspect:
     - `### Flow: <file.function>, <test-path|N/A>` headings
     - `Core files` lists
     - Mermaid node file references
   - Confirm referenced files exist.
   - Flag broken paths and stale renamed/deleted references.
3. Validate test mapping for each flow (docs -> tests).
   - For every flow row/heading with a concrete test path, confirm the test file exists.
   - Confirm at least one test in that file is relevant to the documented flow.
   - If a flow is `N/A`, treat as acceptable only when the plan explicitly justifies it.
4. Validate code-to-doc parity with a second agent (code -> docs).
   - Spawn a second agent dedicated to code-first discovery.
   - Primary agent responsibility: plan-first verification (steps 1-3).
   - Second agent responsibility:
     - scan changed and adjacent code paths,
     - identify major implemented flows not represented in plans,
     - report missing plan coverage and suggested owning plan.
   - Merge findings and de-duplicate before final report.
5. Validate docs do not over-claim implementation.
   - If a plan claims `documentation` status, verify code/test evidence exists.
   - Flag behavior documented as implemented when code is absent or materially different.
6. Produce a structured findings report.
   - Severity levels: `Critical`, `Major`, `Minor`, `Nitpick`.
   - Include exact `path:line` references in plans/tests/code.
   - Include matrix buckets:
     - `extra`: docs/catalog entries that have no valid code/test target (stale or deleted)
     - `missing`: implemented flows/surfaces that are not represented in plans
     - `different`: docs and code both exist but contract or test mapping diverges
     - `wrong`: ownership or plan boundary claims are attached to the wrong plan
   - Include concrete findings for:
     - Missing file references
     - Missing/stale test mappings
     - Missing major documented flows in code
     - Missing major code flows in docs
     - Catalog/index inconsistencies
7. Resolve or document deferrals.
   - Fix straightforward drift immediately when requested.
   - For deferred items, add explicit TODOs with owning plan and file targets.
8. Cleanup generated artifacts.
   - After providing the findings summary, delete generated checklist files:
     - `rm -rf docs/plans/checklists`
   - Keep only source instructions/templates/scripts in `.agent/skills/detect-drift/**`.

## Context

This skill is a bidirectional contract audit with generated checklists:

- Plans -> Code: ensure documented flows/files/tests are real.
- Code -> Plans: ensure major implemented flows are documented in the right plan.
- Plans -> Checklist Artifacts: create actionable audit lists per plan and per UI surface page.

The goal is to prevent silent drift between source-of-truth plans and actual implementation.

## Checklist Generation

- Generator: `.agent/skills/detect-drift/scripts/generate_checklists.py`
- Templates:
  - `.agent/skills/detect-drift/templates/plan-checklist-template.md`
  - `.agent/skills/detect-drift/templates/ui-surface-checklist-template.md`
- Output:
  - `docs/plans/checklists/DRIFT-SUMMARY.md`
  - `docs/plans/checklists/plans/*.md`
  - `docs/plans/checklists/ui-surfaces/*.md`

Use generated files to trace every documented flow and every UI entry point surface during drift review.

## Troubleshooting

- Plan references deleted files:
  1. Update plan paths to new locations or mark as intentionally deleted migration history.
  2. Remove temporary refactor tables when migration is complete.
- Tests exist but do not exercise documented flow:
  1. Add/adjust tests or narrow plan claims.
  2. Do not keep broad plan claims without executable coverage.
- Code has major undocumented behavior:
  1. Add flow rows/types to the owning plan.
  2. If ownership is unclear, define ownership first, then document.
- Second agent cannot be used:
  1. Continue with local code-first pass.
  2. Mark report as single-agent audit and note reduced confidence.
