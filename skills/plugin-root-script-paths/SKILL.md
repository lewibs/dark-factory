---
name: plugin-root-script-paths
description: "When an agent calls a plugin script from a Bash tool call, resolve the plugin root from installed_plugins.json at runtime. ${CLAUDE_PLUGIN_ROOT} is only available in hook command environments, not in Bash tool call subprocesses."
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
- **CRITICAL LIMITATION**: `${CLAUDE_PLUGIN_ROOT}` is only injected into **hook command** environments (PreToolUse, PostToolUse, Stop, SubagentStop). It is NOT available in Bash tool call subprocesses that agents execute. Using `${CLAUDE_PLUGIN_ROOT}` in agent instruction body pseudocode results in an empty string expansion and path resolution failure (exit 127).
- For `allowed-tools:` Bash() frontmatter entries: use `${CLAUDE_PLUGIN_ROOT}` (evaluated in hook context — correct) or use a `*` wildcard prefix to match absolute paths.
- For agent instruction body Bash calls: resolve the plugin root at runtime from `installed_plugins.json`:
  ```bash
  PLUGIN_ROOT=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json'))); print(list(d['plugins'].values())[0][0]['installPath'])")
  bash "$PLUGIN_ROOT/agents/dark-factory/scripts/foo.sh"
  ```
