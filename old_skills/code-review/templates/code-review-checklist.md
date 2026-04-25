# Code Review Checklist

## Scope

- [ ] Reviewed all changed files in diff.
- [ ] Mapped changes to relevant `docs/plans/*.md` contracts.

## 1) Plan Alignment

- [ ] Code behavior matches documented plan Inputs/Outputs.
- [ ] Code behavior matches documented flow paths and contract tables.
- [ ] No untracked plan drift (or drift explicitly documented as a finding).
- [ ] If no plan exists for a changed behavior, flagged as a finding.

## 2) Test Harness and Flow Coverage

- [ ] Each relevant plan flow has executable tests or explicit `N/A` waiver.
- [ ] Happy path coverage is present.
- [ ] Error path coverage is present.
- [ ] Important edge path coverage is present.
- [ ] Tests validate contract behavior, not just internal implementation details.

## 3) Engineering Quality (DRY/YAGNI + Good Practices)

- [ ] DRY: no unnecessary duplicated logic.
- [ ] YAGNI: no speculative abstractions/features beyond plan scope.
- [ ] Naming, readability, and error handling are clear.
- [ ] No obvious correctness or maintainability regressions.

## Findings Output Format

- [ ] Findings sorted by severity: `Critical` -> `Major` -> `Minor` -> `Nitpick`.
- [ ] Every finding includes exact `path:line` and concrete impact.
- [ ] Brief summary provided only after findings.
