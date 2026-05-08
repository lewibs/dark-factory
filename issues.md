# Code Review Issues

## Summary
- Total issues: 4
- Resolved: 4
- Unresolved: 0

## Issues

### issue-1 [CRITICAL] agents/dark-factory/agents/dark-factory-agent.md
- **Status**: [x] Resolved (2026-05-08 12:00)
- **Description**: Plugin root resolution uses fragile list indexing that breaks if multiple plugins are installed. Should explicitly look for 'dark-factory' plugin by name.
- **Resolution**: Updated to use d['plugins'].get('dark-factory@dark-factory') explicit lookup instead of list(d['plugins'].values())[0][0]. Applied in Step 2 and cleanup function.

### issue-2 [MAJOR] agents/dark-factory/agents/dark-factory-agent.md
- **Status**: [x] Resolved (2026-05-08 12:00)
- **Description**: Missing error handling for JSON parsing in plugin root resolution. If installed_plugins.json is missing/corrupt, PLUGIN_ROOT becomes empty and scripts fail silently.
- **Resolution**: Added validation: "If PLUGIN_ROOT is empty: report error and STOP" after resolution in Step 2. Also added error handling in cleanup() and updated skill documentation with bash error check.

### issue-3 [MEDIUM] agents/dark-factory/agents/dark-factory-agent.md
- **Status**: [x] Resolved (2026-05-08 12:00)
- **Description**: Plugin root is resolved THREE times (Steps 2 and 12), causing redundant file I/O and JSON parsing. Should resolve once and reuse variable throughout agent execution.
- **Resolution**: Removed redundant resolution in Step 12; added comment "PLUGIN_ROOT was resolved in Step 2 and is reused here (no redundant file I/O)". Variable now persists throughout agent execution.

### issue-4 [MINOR] agents/dark-factory/agents/dark-factory-agent.md
- **Status**: [x] Resolved (2026-05-08 12:00)
- **Description**: Error handling is inconsistent: Step 2 requires success, but Step 12 ignores metrics errors with "|| true". Should add clarifying comments about why this difference exists.
- **Resolution**: Added comment in Step 12: "Metrics update errors are non-critical; use || true to continue even if script fails" explaining the intentional inconsistency.
