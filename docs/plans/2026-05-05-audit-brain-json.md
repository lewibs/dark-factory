# Plan: Fix brain-patch.json Silent Skip — Use Pointer File Fallback

## Problem

Every agent that writes `brain-patch.json` does so via `$DARK_FACTORY_WORK_DIR/brain-patch.json` and has the rule: **"skip silently if `DARK_FACTORY_WORK_DIR` is unset."**

`DARK_FACTORY_WORK_DIR` is set once by dark-factory-agent but is **not propagated to sub-agents** (Claude Code resets env vars between Bash calls; sub-agents run in isolated processes). This means every single brain-patch.json write is silently skipped in practice — `prUrl`, `planFilePath`, `docsWritten`, and `skillsWritten` are never written to brain.json.

The `/tmp/dark-factory-work-dir` pointer file exists as a documented fallback for exactly this case. Agents don't use it.

## Root Cause

Agents that write brain-patch.json:
1. `feature-agent` — writes `planFilePath`
2. `pr-agent` — writes `prUrl`
3. `skill-update-agent` — writes `skillsWritten`
4. `update-documentation-agent` — writes `docsWritten`
5. `debugger-agent` — writes `bugFiles`

All five silently skip if `DARK_FACTORY_WORK_DIR` is unset. None fall back to `/tmp/dark-factory-work-dir`.

## Fix

Update the brain-patch.json write instruction in all five agents to:

```
WORK_DIR = $DARK_FACTORY_WORK_DIR
if WORK_DIR is empty: WORK_DIR = contents of /tmp/dark-factory-work-dir (if the file exists)
if WORK_DIR is still empty: skip silently
else: write $WORK_DIR/brain-patch.json: { ... }
```

## Flows

### Flow 1: fix-feature-agent-brain-patch
Update `agents/featurework/agents/feature-agent.md` brain-patch.json write rule to use pointer file fallback.

### Flow 2: fix-pr-agent-brain-patch
Update `agents/pr/agents/pr-agent.md` brain-patch.json write rule to use pointer file fallback.

### Flow 3: fix-skill-update-agent-brain-patch
Update `agents/skill-update/agents/skill-update-agent.md` brain-patch.json write rule to use pointer file fallback.

### Flow 4: fix-update-documentation-agent-brain-patch
Update `agents/documentation/agents/update-documentation-agent.md` brain-patch.json write rule to use pointer file fallback.

### Flow 5: fix-debugger-agent-brain-patch
Update `agents/debugger/agents/debugger-agent.md` brain-patch.json write rule to use pointer file fallback.

### Flow 6: add-tests
Add pytest tests verifying that each agent's brain-patch.json write instruction includes the pointer file fallback pattern.

## Files

- `agents/featurework/agents/feature-agent.md`
- `agents/pr/agents/pr-agent.md`
- `agents/skill-update/agents/skill-update-agent.md`
- `agents/documentation/agents/update-documentation-agent.md`
- `agents/debugger/agents/debugger-agent.md`
- `tests/test_brain_patch_pointer_fallback.py` (new)
