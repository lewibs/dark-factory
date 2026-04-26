---
name: classification-table-ordering
description: "When adding a route to the dark-factory-agent classification table, place more-specific signal strings before any signal that is a substring of them to prevent false first-match."
user-invocable: false
---
## When to use

Any time a new route (or new signal strings) is added to the `## Classification rules` table in `agents/dark-factory/agents/dark-factory-agent.md`.

## Steps

1. List all signal strings across every row of the classification table.
2. For every pair of signals, check whether one is a substring of the other (case-insensitive).
   - Example: "quick fix" contains "fix", so "quick fix" must appear in an earlier row than "fix".
3. Place the more-specific (longer / more-constrained) signal in a row that precedes the row containing the substring it overlaps with.
4. Because matching is first-match-wins, the order of rows is the order of evaluation — verify the final table reads top-to-bottom from most-specific to most-general.

## Notes

- The collision does not cause a compile or runtime error; it silently routes the wrong task to the wrong agent. Always audit ordering after edits.
- If two signals are independent (neither is a substring of the other), their relative order does not matter for correctness, but prefer alphabetical or by-specificity for readability.
- The repair-agent signals ("small change", "tweak", "rename", "minor update", "quick fix", "adjust", "alter") were placed before "fix"/"bug"/"crash" specifically because "quick fix" contains "fix".
