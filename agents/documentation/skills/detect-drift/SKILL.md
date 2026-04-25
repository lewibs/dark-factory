---
name: detect-drift
description: Audit parity between documentation/plans and actual implementation. Works for both docs/docs/ system documents and docs/plans/ plan files. Use when validating ship readiness, checking whether documented flows/files/tests match implemented code, or verifying that major implemented flows are not missing from docs or plans.
---

## Required

Use this skill whenever drift may exist between documentation (plans or docs) and code.

1. Determine audit target:
   - **Plans audit**: targets `docs/plans/*.md` — checks plan flow/file/test references against code.
   - **Docs audit**: targets `docs/docs/*.md` — checks documented system behavior against code.
   - Both can be run together.

2. Build inventory and baseline checklist artifacts.
   - For plans: read `docs/index.md` (fallback to `docs/plans/index.md` for legacy repos). Enumerate all plan docs in `docs/plans/*.md`. Flag catalog drift (listed-but-missing, unlisted-but-present).
   - For docs: enumerate all files in `docs/docs/*.md`. Check that each documented system still exists in the codebase.
   - Generate checklists:
     - `python agents/documentation/skills/detect-drift/scripts/generate_checklists.py`
   - Review:
     - `docs/plans/checklists/DRIFT-SUMMARY.md`
     - `docs/plans/checklists/plans/*.md`
     - `docs/plans/checklists/ui-surfaces/*.md`
   - Temporary artifact rule: files under `docs/plans/checklists/` are process-only. Delete them after reporting findings.

3. Validate references (docs/plans -> code).
   - For each plan or doc, inspect:
     - `### Flow: <file.function>, <test-path|N/A>` headings
     - `Core files` lists
     - Mermaid node file references
   - Confirm referenced files exist.
   - Flag broken paths and stale renamed/deleted references.

4. Validate test mapping for each flow (docs/plans -> tests).
   - For every flow row/heading with a concrete test path, confirm the test file exists.
   - Confirm at least one test in that file is relevant to the documented flow.
   - If a flow is `N/A`, treat as acceptable only when the doc/plan explicitly justifies it.

5. Validate code-to-doc parity with a second agent (code -> docs/plans).
   - Spawn a second agent dedicated to code-first discovery.
   - Primary agent responsibility: doc/plan-first verification (steps 2-4).
   - Second agent responsibility:
     - scan changed and adjacent code paths,
     - identify major implemented flows not represented in any plan or doc,
     - report missing coverage and suggested owning doc/plan.
   - Merge findings and de-duplicate before final report.

6. Validate docs/plans do not over-claim implementation.
   - If a plan claims `documentation` status, verify code/test evidence exists.
   - If a doc claims a system behavior, verify the code matches.
   - Flag behavior documented as implemented when code is absent or materially different.

7. Produce a structured findings report.
   - Severity levels: `Critical`, `Major`, `Minor`, `Nitpick`.
   - Include exact `path:line` references in plans/docs/tests/code.
   - Include matrix buckets:
     - `extra`: doc/plan entries that have no valid code/test target (stale or deleted)
     - `missing`: implemented flows/surfaces not represented in any doc or plan
     - `different`: doc/plan and code both exist but contract or test mapping diverges
     - `wrong`: ownership or boundary claims attached to the wrong doc/plan

8. Resolve or document deferrals.
   - Fix straightforward drift immediately when requested.
   - For deferred items, add explicit TODOs with owning doc/plan and file targets.

9. Cleanup generated artifacts.
   - After providing the findings summary, delete generated checklist files:
     - `rm -rf docs/plans/checklists`

## Context

This skill is a bidirectional contract audit:

- Plans/Docs -> Code: ensure documented flows/files/tests are real.
- Code -> Plans/Docs: ensure major implemented flows are documented.
- Plans -> Checklist Artifacts: create actionable audit lists per plan and per UI surface.

The goal is to prevent silent drift between source-of-truth documentation and actual implementation.

## Checklist Generation

- Generator: `agents/documentation/skills/detect-drift/scripts/generate_checklists.py`
- Templates:
  - `agents/documentation/skills/detect-drift/templates/plan-checklist-template.md`
  - `agents/documentation/skills/detect-drift/templates/ui-surface-checklist-template.md`
- Output (temporary):
  - `docs/plans/checklists/DRIFT-SUMMARY.md`
  - `docs/plans/checklists/plans/*.md`
  - `docs/plans/checklists/ui-surfaces/*.md`

## Troubleshooting

- Doc/plan references deleted files:
  1. Update paths to new locations or mark as intentionally deleted migration history.
  2. Remove temporary refactor tables when migration is complete.
- Tests exist but do not exercise documented flow:
  1. Add/adjust tests or narrow doc/plan claims.
  2. Do not keep broad claims without executable coverage.
- Code has major undocumented behavior:
  1. Add flow rows/types to the owning plan or doc.
  2. If ownership is unclear, define ownership first, then document.
- Second agent cannot be used:
  1. Continue with local code-first pass.
  2. Mark report as single-agent audit and note reduced confidence.
