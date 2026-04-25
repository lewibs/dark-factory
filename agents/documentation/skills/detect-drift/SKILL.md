---
name: detect-drift
description: Audit parity between docs/docs/ system documentation and actual implementation. Detects stale references, undocumented flows, and broken behavioral claims. Use when validating whether documented systems match implemented code.
---

## Required

Use this skill whenever drift may exist between `docs/docs/` system documentation and code.

1. Determine audit target:
   - **Docs audit**: targets `docs/docs/*.md` — checks documented system behavior against code.
   - A specific doc file can be targeted instead of the full directory.

2. Build inventory and baseline checklist artifacts.
   - Enumerate all files in `docs/docs/*.md`. Check that each documented system still exists in the codebase.
   - Generate checklists:
     - `python agents/documentation/skills/detect-drift/scripts/generate_checklists.py`
   - Review:
     - `tmp/drift-checklists/DRIFT-SUMMARY.md`
     - `tmp/drift-checklists/docs/*.md`
   - Temporary artifact rule: files under `tmp/drift-checklists/` are process-only. Delete them after reporting findings.

3. Validate references (docs -> code).
   - For each doc, inspect:
     - `### Flow: <file.function>, <test-path|N/A>` headings
     - `Core files` lists
     - Mermaid node file references
   - Confirm referenced files exist.
   - Flag broken paths and stale renamed/deleted references.

4. Validate test mapping for each flow (docs -> tests).
   - For every flow row/heading with a concrete test path, confirm the test file exists.
   - Confirm at least one test in that file is relevant to the documented flow.
   - If a flow is `N/A`, treat as acceptable only when the doc explicitly justifies it.

5. Validate code-to-doc parity with a second agent (code -> docs).
   - Spawn a second agent dedicated to code-first discovery.
   - Primary agent responsibility: doc-first verification (steps 2-4).
   - Second agent responsibility:
     - scan changed and adjacent code paths,
     - identify major implemented flows not represented in any doc,
     - report missing coverage and suggested owning doc.
   - Merge findings and de-duplicate before final report.

6. Validate docs do not over-claim implementation.
   - If a doc claims a system behavior, verify the code matches.
   - Flag behavior documented as implemented when code is absent or materially different.

7. Produce a structured findings report.
   - Severity levels: `Critical`, `Major`, `Minor`, `Nitpick`.
   - Include exact `path:line` references in docs/tests/code.
   - Include matrix buckets:
     - `extra`: doc entries that have no valid code/test target (stale or deleted)
     - `missing`: implemented flows/surfaces not represented in any doc
     - `different`: doc and code both exist but contract or test mapping diverges
     - `wrong`: ownership or boundary claims attached to the wrong doc

8. Resolve or document deferrals.
   - Fix straightforward drift immediately when requested.
   - For deferred items, add explicit TODOs with owning doc and file targets.

9. Cleanup generated artifacts.
   - After providing the findings summary, delete generated checklist files:
     - `rm -rf tmp/drift-checklists`

## Context

This skill is a bidirectional contract audit:

- Docs -> Code: ensure documented flows/files/tests are real.
- Code -> Docs: ensure major implemented flows are documented.
- Docs -> Checklist Artifacts: create actionable audit lists per doc.

The goal is to prevent silent drift between source-of-truth documentation and actual implementation.

## Checklist Generation

- Generator: `agents/documentation/skills/detect-drift/scripts/generate_checklists.py`
- Templates:
  - `agents/documentation/skills/detect-drift/templates/plan-checklist-template.md`
- Output (temporary):
  - `tmp/drift-checklists/DRIFT-SUMMARY.md`
  - `tmp/drift-checklists/docs/*.md`

## Troubleshooting

- Doc references deleted files:
  1. Update paths to new locations or mark as intentionally deleted migration history.
  2. Remove temporary refactor tables when migration is complete.
- Tests exist but do not exercise documented flow:
  1. Add/adjust tests or narrow doc claims.
  2. Do not keep broad claims without executable coverage.
- Code has major undocumented behavior:
  1. Add flow rows/types to the owning doc.
  2. If ownership is unclear, define ownership first, then document.
- Second agent cannot be used:
  1. Continue with local code-first pass.
  2. Mark report as single-agent audit and note reduced confidence.
