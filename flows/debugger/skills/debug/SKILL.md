---
name: systematic-debugging
description: Run a mandatory debugging workflow for non-obvious bugs using the Lewibs bug template and Solving a Bug checklist, then save a deduplicated audit log in docs/bugs. Use when root cause is unclear, issue behavior is not simple/obvious, or repeated guessing risks regressions.
---

# Systematic Debugging

Follow this skill every time debugging is required and the issue is not simple or obvious.

## Steps

1. Confirm this workflow is required:
   - Use this skill for non-obvious, state-dependent, intermittent, multi-system, or unknown-cause bugs.
   - Skip only when the issue is trivial and immediately proven.
2. Stop guessing and create or reopen a bug file in `docs/bugs/`:
   - Use file naming: `docs/bugs/<yyyy-mm-dd>-<bug-slug>.md`.
   - Search existing `docs/bugs/*.md` for the same failure signature/root cause before creating a new file.
   - If the same bug was already solved, update the existing file and do not create a duplicate.
3. Inspect debugger output before changing code:
   - Read all relevant stack traces, runtime logs, and debugger logs for the failing path.
   - Compare current logs with prior bug logs to find similar known failures and reuse validated guidance when applicable.
4. Fill the bug file from `templates/bug-audit-log-template.md`. Do not invent alternate section order.
5. Run the debugging checklist in order:
   - Stop thinking - make an audit log.
   - Read the bug.
   - Make it fail by writing an automated reproduction test first (unit test preferred; integration/e2e when unit is not feasible), and record exact steps.
   - Understand the system boundary and flow.
   - Run the reproduction test to confirm it fails before the fix.
   - Identify the cause of failure from evidence.
   - Fix the root problem (never just symptoms).
   - Re-run the reproduction test and failure steps to confirm the issue is resolved.
   - Remove the fix and confirm the bug fails again (when safe) to prove causality.
6. Verify and finalize:
   - Keep the repro test as a regression guard when appropriate.
   - Record final root cause, fix summary, and verification evidence in the bug file.
   - Ensure one saved audit log per unique solved root cause; merge duplicates into the existing bug file.
7. Run a final code review gate by invoking `.agent/skills/code-review/SKILL.md`:
   - Validate the fix diff against plan contracts.
   - Validate plan-flow test harness coverage for the fix paths.
   - Validate DRY/YAGNI and maintainability before closing the bug.

## Resources
- Related skill: `.agent/skills/code-review/SKILL.md` for end-of-fix quality gate.
- Related skill: `.agent/skills/manage-wiki/SKILL.md` for doc index and nav consistency.

## Notes

- Never ship a workaround without root-cause evidence.
- Never close a debug task without updating `docs/bugs/` (new or existing file).
- Never close a debug task before running `code-review` on the fix diff.
- Never keep duplicate solved-bug logs for the same issue/root cause.

## Template

Use `templates/bug-audit-log-template.md` as the required scaffold for bug audit logs.
