---
name: plugin-root-script-paths
description: "When an agent, command, or skill calls a script bundled inside the dark-factory plugin, always prefix the path with ${CLAUDE_PLUGIN_ROOT}/ instead of using a bare relative path."
user-invocable: false
---
## When to use

Any time you write or edit an agent (`.md` in `agents/`), a command (`.md` in `commands/`), or a skill (`SKILL.md` in `skills/`) that invokes a script (`bash`, `python3`, etc.) that ships inside the dark-factory plugin repository.

This applies to:
- `bash <script>.sh` calls
- `python3 <script>.py` calls
- `allowed-tools:` Bash() entries that include a script path
- `scripts:` frontmatter declarations in agent files
- Prose pseudocode inside agent instruction bodies

## Steps

1. Identify every script reference that uses a bare relative path such as:
   - `bash agents/dark-factory/scripts/foo.sh`
   - `python3 scripts/bar.py`
2. Replace each bare relative path with the `${CLAUDE_PLUGIN_ROOT}/` prefix:
   - `bash "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/foo.sh"`
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bar.py"`
3. Apply the same replacement in `allowed-tools:` Bash() entries:
   - Before: `Bash(bash agents/dark-factory/scripts/foo.sh *)`
   - After: `Bash(bash ${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/foo.sh *)`
4. Apply the same replacement in `scripts:` frontmatter lines.
5. Double-quote the expanded path in shell contexts to handle spaces:
   - `bash "${CLAUDE_PLUGIN_ROOT}/scripts/foo.sh"` (not `bash $CLAUDE_PLUGIN_ROOT/scripts/foo.sh`)

## Notes

- `${CLAUDE_PLUGIN_ROOT}` is injected by the Claude Code plugin runtime and resolves to the absolute directory where the plugin is installed. Bare relative paths break when the plugin is installed at a location different from the current working directory of the Claude process.
- Relative paths like `bash scripts/foo.sh` look correct in development (when CWD is the repo root) but fail silently in production installs.
- Skills that reference their own helper scripts (e.g. `mermaid_to_image.py`) must use `${CLAUDE_PLUGIN_ROOT}` too — they are bundled plugin assets, not project-local files.
- The `${CLAUDE_PLUGIN_ROOT}` variable is available in hook commands, agent pseudocode, and allowed-tool patterns alike.
