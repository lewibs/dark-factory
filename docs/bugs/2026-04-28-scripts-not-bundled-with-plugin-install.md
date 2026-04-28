# Bug Audit Log: Scripts Not Bundled with Plugin Install

**Date:** 2026-04-28
**Severity:** Critical
**Status:** Fixed

---

## Failure Signature

When the dark-factory plugin is installed via `claude plugin install dark-factory`, the hook commands in `.claude/settings.json` and the script references in agent instruction files use relative paths (e.g., `bash agents/dark-factory/scripts/pre-tool-use-hook.sh`). These paths are resolved relative to the user's project CWD, not the plugin install directory, so the scripts cannot be found.

---

## Symptoms

- `bash agents/dark-factory/scripts/pre-tool-use-hook.sh` fails with "No such file or directory" when Claude runs from a user project directory
- `bash agents/dark-factory/scripts/post-tool-use-hook.sh` same failure
- `bash agents/dark-factory/scripts/cleanup-worktree.sh` same failure
- `bash agents/dark-factory/scripts/prep-feature-dir.sh` fails when dark-factory-agent runs
- `python3 scripts/update-metrics.py` fails in dark-factory-agent cleanup
- `python3 scripts/render_section.py` fails in feature-agent
- `python3 scripts/mermaid_to_image.py` fails in sub-planning-agent
- Brain state management (pre/post hooks) is completely broken for installed plugin users

---

## Root Cause

The `.claude/settings.json` hooks and agent instruction files use relative paths to scripts. When the dark-factory plugin is installed globally (via `claude plugin install`), Claude Code runs from the **user's project directory**, not the plugin install directory. Relative paths like `bash agents/dark-factory/scripts/pre-tool-use-hook.sh` resolve against the user's CWD, where these scripts do not exist.

The Claude Code plugin system provides the `${CLAUDE_PLUGIN_ROOT}` environment variable which resolves to the plugin's install directory. This variable must be used for all script references in:
- Hook commands (in `hooks/hooks.json`)
- Agent `allowed-tools` frontmatter
- Agent instruction bodies

Additionally, the hooks should be defined in `hooks/hooks.json` (the standard plugin hook format) rather than `.claude/settings.json`.

---

## Evidence

- `installed_plugins.json` shows `installPath: /home/lewibs/.claude/plugins/cache/dark-factory/dark-factory/1.2.20`
- `.claude/settings.json` hooks: `"command": "bash agents/dark-factory/scripts/pre-tool-use-hook.sh"` — no absolute path
- The `hookify` and `ralph-loop` official plugins use `${CLAUDE_PLUGIN_ROOT}` correctly in `hooks/hooks.json`
- `ralph-loop` command `.md` uses `allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-ralph-loop.sh:*)"]` showing the pattern for agent files too

---

## Fix Summary

1. Created `hooks/hooks.json` with hook commands using `${CLAUDE_PLUGIN_ROOT}` absolute paths
2. Added `"hooks": "./hooks/hooks.json"` to `.claude-plugin/plugin.json`
3. Removed duplicate hook definitions from `.claude/settings.json`
4. Updated `agents/dark-factory/agents/dark-factory-agent.md` allowed-tools and script invocations to use `${CLAUDE_PLUGIN_ROOT}`
5. Updated `agents/featurework/agents/feature-agent.md` script invocations to use `${CLAUDE_PLUGIN_ROOT}`
6. Updated `agents/featurework/planning/agents/sub-planning-agent.md` to use `${CLAUDE_PLUGIN_ROOT}`

---

## Verification

- `hooks/hooks.json` created with correct `${CLAUDE_PLUGIN_ROOT}` paths
- `.claude/settings.json` no longer contains hook definitions
- `plugin.json` references `./hooks/hooks.json`
- All agent files updated with `${CLAUDE_PLUGIN_ROOT}` script paths
