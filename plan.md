# Plan: Fix PR Description Generation — Route-Specific Content Sourcing

## System Intent

The pr-agent previously used a single code path for PR body generation regardless of work route:
`Populate Description from planFilePath (or description string).`

This meant debug flows got no description (planFilePath is null for debugger-agent) and repair flows had no way to auto-generate content. The fix makes pr-agent read `classification` from brain.json and apply route-appropriate sourcing.

## Scope

### Files Modified
1. `agents/pr/agents/pr-agent.md` — Step 1: replace single-path description logic with route-specific IF/ELSE

### Changes

#### pr-agent.md — Step 1 (Build PR Body)

**Before**:
```
Populate Description from planFilePath (or description string).
```

**After**:
- Read `classification` from brain.json (injected via pre-hook)
- `feature`: read planFilePath verbatim
- `debugger`: search `$PROJECT_DIR/docs/bugs/` for .md matching `taskName` (exact/prefix or most recent); read verbatim
- `repair` / `fix-flow`: use planFilePath if provided, else generate from `git log` + `git diff --name-only` summary
- Fallback (unknown classification): planFilePath or description string

## Flows

### Flow 1: feature route
Entry: pr-agent Step 1, classification == "feature"
Steps: read planFilePath from brain → read file verbatim → populate Description
Exit: PR body contains full plan

### Flow 2: debugger route
Entry: pr-agent Step 1, classification == "debugger"
Steps: glob $PROJECT_DIR/docs/bugs/*.md → find file matching taskName → read verbatim → populate Description
Exit: PR body contains full bug doc

### Flow 3: repair/fix-flow route
Entry: pr-agent Step 1, classification == "repair" or "fix-flow"
Steps: if planFilePath → read it; else run git log + git diff --name-only → format summary → populate Description
Exit: PR body contains meaningful description of changes

## Files Written
- `agents/pr/agents/pr-agent.md` — route-specific description sourcing logic
