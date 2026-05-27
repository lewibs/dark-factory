---
name: remove-stale-agents
description: "Audit agents/ for deprecated or unreachable agent files and delete them. Use when the architecture evolves and old orchestrators are replaced by commands."
user-invocable: false
---
## When to use

When an agent file meets both conditions:
1. Its `description:` frontmatter contains `[DEPRECATED]` (or equivalent marker), **and**
2. No active command file in `agents/commands/` references or invokes it.

This pattern recurs whenever a monolithic orchestrator is replaced by standalone commands — the old agent file lingers as dead weight.

## Steps

1. **Find all deprecated agent files:**
   ```bash
   grep -r "\[DEPRECATED\]\|DEPRECATED" agents/ --include="*.md" -l
   ```

2. **For each deprecated file, check if any active command invokes it:**
   ```bash
   AGENT_NAME="<agent-slug>"
   grep -r "$AGENT_NAME" agents/commands/ --include="*.md" -l
   ```
   If the grep returns nothing, the agent is unreachable from any command.

3. **Also check non-command agent files for cross-references:**
   ```bash
   grep -r "$AGENT_NAME" agents/ --include="*.md" -l | grep -v "$AGENT_NAME.md"
   ```
   If only the file itself shows up, it is safe to delete.

4. **Delete the confirmed-unreachable agent file:**
   ```bash
   git rm agents/<group>/agents/<agent-slug>.md
   ```

5. **Delete or archive the corresponding docs file** (if one exists):
   ```bash
   ls docs/docs/<agent-slug>.md 2>/dev/null && git rm docs/docs/<agent-slug>.md
   ```

6. **Run the test suite** to confirm no test references the deleted agent by name:
   ```bash
   pytest
   ```
   Fix any broken assertions before committing.

7. **Final grep** to verify zero remaining references to the deleted agent slug:
   ```bash
   grep -r "<agent-slug>" . --include="*.md" --include="*.sh" --include="*.json" \
     --include="*.py" --exclude-dir=".git"
   ```

## Notes

- A `[DEPRECATED]` description alone is not sufficient — the agent must also be unreachable from all active commands. An agent can be deprecated but still invoked transitionally.
- Check `agents/commands/` first (the primary dispatch layer), then scan all other agent `.md` files for `invoke` or `agent:` references.
- Deleting the agent file without removing its `docs/docs/` counterpart leaves stale documentation — always clean up both.
- If tests reference the agent's name as a string (e.g., in `test_manufacture_flow_violations.py`), remove or update those assertions too before the commit passes.
- This pattern typically surfaces after an architectural migration (e.g., replacing a single orchestrator with multiple standalone commands). Plan for it as a cleanup task at the end of any such migration.
