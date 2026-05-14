# Remove Fix-Flow Route from Dark-Factory

## Summary

Delete the `fix-flow` route entirely from dark-factory since only the debugger is needed going forward. This involves:
1. Removing the `fix-flow-orchestrator` agent and all its dependencies
2. Removing the `fix-flow` classification route from `dark-factory-agent`
3. Cleaning up any orphaned skills, agents, or scripts that only `fix-flow` used
4. Updating tests and documentation to remove fix-flow references

## Scope

### Files/Directories to Delete
- `agents/fixflow/` — entire fix-flow orchestrator and sub-agents
- Any skills that are ONLY used by fix-flow
- Any scripts that are ONLY used by fix-flow
- Test files specific to fix-flow

### Files to Modify
- `agents/dark-factory/agents/dark-factory-agent.md` — remove fix-flow route (lines 81)
- `task-classifier.md` (or skills) — remove fix-flow classification option
- `plugin.json` — if fix-flow agents are registered
- README.md — remove fix-flow mentions
- Any integration test files

### Investigation Needed
1. Grep for all `fix-flow` references in codebase
2. Identify which agents/skills/commands are ONLY used by fix-flow
3. Verify debugger-agent covers all necessary use cases

## Implementation Checklist

- [ ] Investigate all fix-flow references
- [ ] Identify orphaned dependencies
- [ ] Delete fix-flow-orchestrator agent directory
- [ ] Remove fix-flow route from dark-factory-agent
- [ ] Remove fix-flow option from task-classifier
- [ ] Delete orphaned skills and scripts
- [ ] Update plugin.json if needed
- [ ] Update README and docs
- [ ] Remove fix-flow tests
- [ ] Test dark-factory with remaining routes
- [ ] Commit all changes

## Flows

This is a system deletion flow with no branching.

