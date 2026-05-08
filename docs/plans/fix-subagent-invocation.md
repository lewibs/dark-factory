# Fix subagent invocation in execution-agent and fix-flow-orchestrator

## Status

approved

## Summary

Replace ambiguous "Spawn X" instructions in execution-agent and fix-flow-orchestrator with explicit Agent tool invocations using proper subagent_type references. This improves clarity and ensures correct agent routing.

## Problem Statement

**execution-agent** currently uses vague language like:
- "Spawn `skeleton-agent` with `planPath`"
- "Spawn `testing-agent` with `planPath`"
- "Spawn `implementation-agent` with `planPath`"

**fix-flow-orchestrator** uses equally vague instructions:
- "Spawn a sub-agent using investigation-agent"
- "Spawn a sub-agent using setup-wizard"
- "Spawn a sub-agent using the instructions in ralph-fix-and-push"

These "Spawn X" patterns lack explicit subagent_type values and don't follow the documented Agent tool invocation pattern shown in code-review-orchestrator-agent:
```
Invoke Agent tool with subagent_type `dark-factory:code-review:agents:high-level-review-agent`
```

## Affected Systems

1. **execution-agent** (`agents/featurework/execution/agents/execution-agent.md`)
   - Lines with "Spawn" instructions for skeleton-agent, testing-agent, implementation-agent
   
2. **fix-flow-orchestrator** (`agents/fix-flow/agents/fix-flow-orchestrator.md`)
   - Phase 1 investigation-agent invocation
   - Phase 2 setup-wizard invocation
   - Phase 3 ralph-fix-and-push invocation

## Solution

### Phase 1: Implementation

Replace each "Spawn X" with explicit Agent tool call:

**execution-agent changes:**
- Replace "Spawn `skeleton-agent`" with: Invoke Agent tool with subagent_type "dark-factory:featurework:execution:agents:skeleton-agent"
- Replace "Spawn `testing-agent`" with: Invoke Agent tool with subagent_type "dark-factory:featurework:execution:agents:testing-agent"
- Replace "Spawn `implementation-agent`" with: Invoke Agent tool with subagent_type "dark-factory:featurework:execution:agents:implementation-agent"

**fix-flow-orchestrator changes:**
- Replace "Spawn a sub-agent using investigation-agent" with: Invoke Agent tool with subagent_type "dark-factory:investigation-agent"
- Replace "Spawn a sub-agent using setup-wizard" with: Invoke Agent tool with subagent_type "dark-factory:fix-flow:agents:setup-wizard"
- Replace "Spawn a sub-agent using the instructions in ralph-fix-and-push" with: Invoke Agent tool with subagent_type "dark-factory:fix-flow:agents:ralph-fix-and-push"

## Flows

### Flow 1: Update execution-agent

File: `agents/featurework/execution/agents/execution-agent.md`

1. Replace line "2. Spawn `skeleton-agent`..." with explicit Agent tool invocation
2. Replace line "4. Spawn `testing-agent`..." with explicit Agent tool invocation
3. Replace line "5. Spawn `implementation-agent`..." with explicit Agent tool invocation

### Flow 2: Update fix-flow-orchestrator

File: `agents/fix-flow/agents/fix-flow-orchestrator.md`

1. Replace "Spawn a sub-agent using investigation-agent" with explicit Agent tool invocation for investigation-agent
2. Replace "Spawn a sub-agent using setup-wizard" with explicit Agent tool invocation for setup-wizard
3. Replace "Spawn a sub-agent using the instructions in ralph-fix-and-push" with explicit Agent tool invocation for ralph-fix-and-push

## Validation

- All "Spawn" instructions replaced with explicit Agent tool syntax
- Each subagent_type points to a valid agent file in the codebase
- Documentation remains clear and actionable
