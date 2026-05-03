# Skills Directory Refactoring Plan

## Objective
Consolidate all reusable skills into the top-level `/skills/` directory, removing agent-local skill definitions for better organization and maintainability.

## Problem Statement
The codebase had 10 skills defined in `/agents/*/skills/` that violated the organizational principle that all reusable skills should live in `/skills/`:
- `agents/pr/skills/create-pr`
- `agents/documentation/skills/{investigate,documentation,detect-drift}`
- `agents/debugger/skills/debug`
- `agents/fix-flow/skills/generate-{deploy,fetch-logs,trigger,wait-for-completion}`
- `agents/featurework/execution/skills/deviation-protocol`

## Solution
Move all 10 agent-local skills to the top-level `/skills/` directory while preserving all functionality and references.

## Changes Made
1. **Consolidated 10 skills** to `/skills/`:
   - create-pr/SKILL.md
   - debug/SKILL.md + debug/templates/
   - detect-drift/SKILL.md + detect-drift/scripts/ + detect-drift/templates/
   - deviation-protocol/SKILL.md
   - documentation/SKILL.md + documentation/templates/
   - generate-deploy/SKILL.md
   - generate-fetch-logs/SKILL.md
   - generate-trigger/SKILL.md
   - generate-wait-for-completion/SKILL.md
   - investigate/SKILL.md

2. **Removed empty directories**:
   - agents/pr/skills/
   - agents/documentation/skills/
   - agents/debugger/skills/
   - agents/fix-flow/skills/
   - agents/featurework/execution/skills/

## Verification
✓ 0 agent-local skills remain
✓ 56 total skills in /skills/ (46 + 10 moved)
✓ Single commit with clear git renames
✓ All skill definitions preserved with templates and scripts
✓ No functional changes to skill behavior

## Impact
- **Positive**: Cleaner organization, consistent skill location, reduced directory nesting
- **Risk**: None identified — skills are self-contained and all agent references use the Skill tool (which auto-locates skills)
