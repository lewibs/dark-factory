---
name: self-expanding-checklist-loop
description: "Use this skill when building an agent loop that discovers new work items while processing existing ones — the checklist must grow before the current item is marked done to prevent orphaned items."
user-invocable: false
---
## When to use

Any time an agent loop processes items from a checklist and the processing step itself can produce new items that belong in the same checklist. Examples:
- Fixing pipeline violations that introduce new violations
- Refactoring tasks that reveal adjacent technical debt
- Migration passes that expose additional items to migrate

The non-obvious risk: if you mark the current item done before appending new items, and the agent crashes between those two operations, the new items are lost.

## Steps

1. Maintain a markdown checklist file on disk (not in memory) so restarts can resume:
   ```
   # Improvement Checklist
   - [ ] #42 — [Title] (description)
   - [ ] "freeform description" — (freeform)
   ```

2. The main loop reads the checklist file fresh on every iteration — never cache the list in memory across iterations:
   ```
   WHILE TRUE:
     checklistContent = read(checklistPath)
     uncheckedItem = first line matching ^- \[ \]
     if uncheckedItem is null: BREAK
   ```

3. After processing an item, append any newly discovered items to the checklist file **before** marking the current item done:
   ```
   # CORRECT ORDER:
   FOR EACH newItem IN discoveredItems:
     append_to_checklist(checklistPath, newItem)   # 1. grow first
   mark_as_checked(checklistPath, currentItem)      # 2. mark done second

   # WRONG ORDER (loses items on crash):
   mark_as_checked(checklistPath, currentItem)      # 1. mark done
   FOR EACH newItem IN discoveredItems:             # 2. grow — if crash here, items lost
     append_to_checklist(checklistPath, newItem)
   ```

4. Use atomic writes for all checklist mutations — write to a `.tmp.$$` file then `mv` it into place:
   ```bash
   TMP="${CHECKLIST_PATH}.tmp.$$"
   cp "$CHECKLIST_PATH" "$TMP"
   echo "$NEW_ITEM" >> "$TMP"
   mv "$TMP" "$CHECKLIST_PATH"
   ```

5. Add a max-iteration guard (see `agent-loop-with-max-iterations` skill) to prevent infinite loops when discovery always produces new items:
   ```
   MAX_ITERATIONS = 50
   if iterationCount >= MAX_ITERATIONS:
     STOP with error "Exceeded max iterations — manual review required"
   ```

6. Track statistics in a separate variable (not in the checklist file):
   - `totalIssuesFixed` — count of items marked done
   - `totalNewItemsFound` — count of items appended by the discovery step
   - `iterationCount` — total loop passes

## Notes

- The checklist format `- [ ]` / `- [x]` is conventional markdown and readable without special tooling.
- If item discovery can fail non-fatally (e.g., an API call to detect violations), log the failure and continue to the next item rather than halting — partial tracking is better than losing progress.
- The checklist file path should be written to a `$WORK_DIR` that persists across agent restarts; do not use `/tmp`.
- When an item fails to process (not just discovery fails, but the processing itself fails), mark it `- [x] FAILED: ...` rather than removing it — this preserves the audit trail.
