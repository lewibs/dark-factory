# Code Review Plan: SubagentStop Hook Removal from pr-agent

## Task

Remove the SubagentStop hook from pr-agent.md that was destroying the worktree before dark-factory-agent could complete Steps 11-12.

## Context

- **Branch**: feature/debug-agent-flow-stop
- **Bug documented in**: docs/bugs/2026-05-08-pr-agent-cleanup-hook-destroys-worktree-early.md
- **Root cause**: pr-agent.md declared `SubagentStop: "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/pr-agent-cleanup-hook.sh"` which fires when pr-agent stops, BEFORE dark-factory-agent regains control and Steps 11-12 need brain.json
- **Fix applied**: Remove the SubagentStop line from pr-agent.md frontmatter

## Review Scope

### Files Changed
1. **agents/pr/agents/pr-agent.md** — Removed SubagentStop declaration
2. **docs/bugs/2026-05-08-pr-agent-cleanup-hook-destroys-worktree-early.md** — Bug documentation with audit log
3. **docs/docs/pr-agent.md** — Updated documentation clarifying no SubagentStop hook
4. **tests/test_pr_agent_cleanup_hook_conflict.py** — Regression test ensuring fix is maintained

### Review Checklist

1. **SubagentStop Hook Removal**
   - Verify SubagentStop line is completely removed from pr-agent.md YAML frontmatter
   - Confirm no references to pr-agent-cleanup-hook.sh remain in pr-agent.md

2. **No Conflicting Hooks**
   - Check that no other agents in the codebase declare conflicting cleanup hooks
   - Verify pr-agent-cleanup-hook.sh script still exists (preserved for standalone use)
   - Confirm dark-factory-agent.md still has cleanup-worktree.sh invocation in Step 12

3. **pr-agent Lifecycle Integrity**
   - Verify pr-agent.md still has PostToolUse hook (append-footer-hook.sh) — should be unchanged
   - Confirm pr-agent YAML frontmatter is otherwise intact
   - Check that the removal does not break Step 0-5 orchestration

4. **Test Coverage**
   - Verify tests/test_pr_agent_cleanup_hook_conflict.py has appropriate regression tests
   - Check that all 4 test cases are properly written (SubagentStop absent, no cleanup reference, dfa owns cleanup, script exists but not auto-triggered)
   - Confirm tests validate the fix

5. **Documentation Quality**
   - Bug doc explains root cause clearly (SubagentStop fires before Step 11)
   - Documentation includes reproduction path and verification checklist
   - docs/docs/pr-agent.md has clear explanation why no SubagentStop is intentional

## Success Criteria

- SubagentStop hook completely removed from pr-agent.md
- No conflicting cleanup hooks exist in other agents
- pr-agent lifecycle (Steps 0-5) remains valid
- Regression tests pass and cover the fix
- Documentation is clear and comprehensive
- All issues from code review resolved before completion
