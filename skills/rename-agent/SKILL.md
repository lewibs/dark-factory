---
name: rename-agent
description: "Rename an agent file and update all references across agent files, docs, plans, scripts, and brain.json in one consistent pass."
user-invocable: false
---
## When to use
When an agent `.md` file needs to be renamed (slug, filename, or display name change) and all references to it must be kept consistent across the codebase.

## Steps

1. **Rename the file with git mv** so git tracks it as a rename (not delete + create):
   ```bash
   git mv agents/<group>/agents/<old-name>.md agents/<group>/agents/<new-name>.md
   ```

2. **Update the `name:` field in the agent frontmatter** (inside the renamed file itself):
   ```yaml
   name: <new-name>
   ```

3. **Grep for all remaining occurrences of the old name** across the repo:
   ```bash
   grep -r "<old-name>" . --include="*.md" --include="*.sh" --include="*.json" -l
   ```

4. **Update each reference location in this order:**
   - **Caller agent files** (`agents/*/agents/*.md`) — update `description:` fields, orchestration pseudocode, and resource tables that reference the old name or old path
   - **Docs files** (`docs/docs/*.md`) — update prose, Mermaid diagram node labels, pseudocode blocks, and flow path tables
   - **Plan files** (`docs/plans/*.md`) — update any references in plan summaries or pseudocode
   - **Hook scripts** (`agents/*/scripts/*.sh`) — update any string matches on the agent name
   - **`brain.json`** — update `taskName`, `workDir`, and any other fields that embed the agent name

5. **Update Mermaid diagram node labels** — these are easy to miss because they appear inside fenced code blocks. Search specifically:
   ```bash
   grep -r "<old-name>" . --include="*.md" -n | grep -i "mermaid\|flowchart\|graph\|sequenceDiagram" || \
   grep -rn "<old-name>" . --include="*.md"
   ```
   Node labels in Mermaid use the format `NodeId[display label\npath]` — update both the node ID and the display label.

6. **Run the test suite** to verify no hook scripts or tests reference the old name:
   ```bash
   pytest
   ```

7. **Final grep check** — confirm zero remaining references to the old name:
   ```bash
   grep -r "<old-name>" . --include="*.md" --include="*.sh" --include="*.json" --exclude-dir=".git"
   ```

## Notes

- Use `git mv` (not a plain file rename) so that `git diff` shows a rename rather than a delete+add. This matters for PR reviewers and for `git log --follow`.
- Mermaid diagrams inside fenced code blocks are the most commonly missed location — always grep inside `.md` files for the old name, even within code fences.
- The `description:` field in calling agents often embeds the old agent name as a path string — update it to the new path.
- `brain.json` stores the current `taskName` and `workDir` which may encode the old agent name — update them to avoid stale state in subsequent runs.
- If the agent being renamed is referenced in a `pre-tool-use-hook.sh` or `post-tool-use-hook.sh`, update the string match there too; hook scripts key on agent names for routing decisions.
