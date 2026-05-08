# Code Review Plan: Fix repair/debugger stuck issue

## Task
"repair keeps getting stuck after it is classified as repair. debug and fix this so it stops getting stuck."

## Summary of Changes
The fix removes global SubagentStop hooks from `.claude/settings.json` that were causing repair-agent and debugger-agent worktrees to be destroyed prematurely.

### Root Cause
Global SubagentStop hooks in settings.json were firing for ALL sub-agents, including repair-agent and debugger-agent. The pr-agent-cleanup-hook.sh hook was designed only for pr-agent but was running when any agent finished, calling cleanup-worktree.sh which removed the feature worktree before dark-factory-agent could complete its remaining steps.

### Changes Made
1. **`.claude/settings.json`** — Removed all three SubagentStop entries from the global hooks section
2. **`docs/bugs/2026-05-07-repair-debugger-stuck-global-subagent-stop.md`** — Added comprehensive bug audit log documenting the root cause, reproduction, and verification

### Design Rationale
- SubagentStop hooks are properly declared in each agent's YAML frontmatter (per subagent-stop-in-agent-frontmatter skill)
- Global entries in settings.json were redundant and caused unintended side effects
- All agents (pr-agent, repair-agent, debugger-agent) already declare their hooks in frontmatter

## Review Focus Areas
1. Verify the SubagentStop hooks were truly redundant (check that all agents declare them in frontmatter)
2. Confirm no other global hooks should remain in settings.json
3. Ensure the bug audit log is complete and accurate
4. Verify the fix is at the root cause (not a workaround)
5. Check that this won't break any existing agent behavior
