---
name: flow-state-manager
description: "Manages the flow approval state machine during feature planning. Tracks approved flows, current flow, and provides operations to load/save state while orchestrating the multi-flow approval process."
user-invocable: false
---

# flow-state-manager

Track and manage the approval state of individual flows during feature planning.

## Purpose

During the feature planning phase, users must approve each flow one at a time. This skill manages:
- Which flows have been approved
- Which flow is currently being reviewed
- State persistence across re-invocations

## State Schema

The flow approval state is stored in `$DARK_FACTORY_WORK_DIR/flows-state.json`:

```json
{
  "approved": ["flow-name-1", "flow-name-2"],
  "current": "flow-name-3"
}
```

- `approved` — array of flow names that have been approved by the user
- `current` — the flow currently under review (null if no flows are being reviewed)

## Operations

### load(workDir)

Reads flows-state.json from disk. If the file does not exist, initializes empty state.

**Input**:
- `workDir` — absolute path to git worktree (string)

**Output**:
```json
{
  "success": true,
  "state": {
    "approved": [],
    "current": null
  }
}
```

**Error Output**:
```json
{
  "success": false,
  "reason": "Unable to read flows-state.json from <workDir>"
}
```

### save(workDir, state)

Writes flows-state.json to disk.

**Input**:
- `workDir` — absolute path to git worktree (string)
- `state` — state object to write (object)
  ```json
  {
    "approved": ["flow-1", "flow-2"],
    "current": "flow-3"
  }
  ```

**Output**:
```json
{
  "success": true,
  "path": "/path/to/flows-state.json"
}
```

**Error Output**:
```json
{
  "success": false,
  "reason": "Unable to write flows-state.json to <workDir>"
}
```

### markApproved(workDir, flowName)

Adds a flow to the approved list and clears current flow pointer.

**Input**:
- `workDir` — absolute path to git worktree (string)
- `flowName` — name of the flow to approve (string, e.g., "user-login")

**Output**:
```json
{
  "success": true,
  "state": {
    "approved": ["flow-1", "flow-2", "flow-3"],
    "current": null
  }
}
```

**Rules**:
- Does nothing if flow is already in approved list (idempotent)
- After marking approved, sets `current: null` to clear the review pointer

### setCurrentFlow(workDir, flowName)

Sets the flow currently under review.

**Input**:
- `workDir` — absolute path to git worktree (string)
- `flowName` — name of the flow to set as current (string)

**Output**:
```json
{
  "success": true,
  "state": {
    "approved": ["flow-1"],
    "current": "flow-2"
  }
}
```

### getApprovedFlows(workDir)

Returns the list of approved flow names.

**Input**:
- `workDir` — absolute path to git worktree (string)

**Output**:
```json
{
  "success": true,
  "approved": ["flow-1", "flow-2"],
  "count": 2
}
```

### findNextUnapprovedFlow(workDir, allFlowNames)

Finds the first flow in the `allFlowNames` list that is not in the approved list.

**Input**:
- `workDir` — absolute path to git worktree (string)
- `allFlowNames` — array of all flow names from the plan (array of strings)
  ```json
  ["user-login", "payment-processing", "account-creation"]
  ```

**Output** (flow found):
```json
{
  "success": true,
  "nextFlow": "user-login",
  "isLastFlow": false,
  "allApproved": false
}
```

**Output** (all flows approved):
```json
{
  "success": true,
  "nextFlow": null,
  "isLastFlow": true,
  "allApproved": true
}
```

**Error Output**:
```json
{
  "success": false,
  "reason": "Cannot find flows-state.json in <workDir>"
}
```

## Typical Usage Pattern (in feature-agent)

```
# Load current state
state = load(workDir)

# Determine current phase
if answer == "Approve — continue to next flow":
  markApproved(workDir, state.current)

# Find what to show next
nextFlow = findNextUnapprovedFlow(workDir, allFlows)

if nextFlow is null:
  # All flows approved — move to execution
  GOTO phase == "execution"

# Prepare current flow for review
setCurrentFlow(workDir, nextFlow)
# ... render nextFlow section, return question
```

## Rules

- State file location is always `$DARK_FACTORY_WORK_DIR/flows-state.json` (not under version control)
- Flow names must match exactly (case-sensitive) when comparing approved list to all flows
- If a user requests changes to a flow, do NOT mark it approved; just update the plan and re-present the same flow
- All operations are idempotent (calling twice with the same input produces the same result)
