---
name: manage-issues-file
description: "Create, update, and manage the issues.md file during code review. Track review findings and mark them resolved as fixes are applied."
user-invocable: false
---

# manage-issues-file

Manage the issues.md file that tracks code review findings and their resolution status.

## Input

All operations use `workDir` to locate `$workDir/issues.md`.

### Operation: create

Create a new issues.md file with initial review findings.

**Input**:
```json
{
  "operation": "create",
  "workDir": "/path/to/worktree",
  "reviewPoints": [
    {
      "id": "issue-1",
      "severity": "high",
      "component": "auth/login.ts",
      "description": "Missing null check on user object",
      "resolved": false
    }
  ]
}
```

**Output**:
```json
{
  "success": true,
  "path": "/path/to/worktree/issues.md",
  "issueCount": 1
}
```

### Operation: update

Mark an issue as resolved.

**Input**:
```json
{
  "operation": "update",
  "workDir": "/path/to/worktree",
  "issueId": "issue-1",
  "resolved": true,
  "resolution": "Added null check in LoginForm.tsx line 42"
}
```

**Output**:
```json
{
  "success": true,
  "updated": true
}
```

### Operation: read

Read the current issues.md file.

**Input**:
```json
{
  "operation": "read",
  "workDir": "/path/to/worktree"
}
```

**Output**:
```json
{
  "success": true,
  "issues": [
    {
      "id": "issue-1",
      "severity": "high",
      "component": "auth/login.ts",
      "description": "Missing null check on user object",
      "resolved": false
    }
  ],
  "resolvedCount": 0,
  "totalCount": 1
}
```

## Issues.md Format

The issues.md file uses a structured format:

```markdown
# Code Review Issues

## Summary
- Total issues: 3
- Resolved: 1
- Unresolved: 2

## Issues

### issue-1 [HIGH] auth/login.ts
- **Status**: [x] Resolved (2024-03-15 12:30)
- **Description**: Missing null check on user object
- **Resolution**: Added null check in LoginForm.tsx line 42

### issue-2 [MEDIUM] api/auth.ts
- **Status**: [ ] Unresolved
- **Description**: Unused import statement
- **Resolution**: _pending_

### issue-3 [LOW] styles/login.css
- **Status**: [ ] Unresolved
- **Description**: Color contrast accessibility issue
- **Resolution**: _pending_
```

## Rules

- Issues are identified by `id` (e.g., "issue-1", "issue-2")
- Severity levels are HIGH, MEDIUM, LOW
- Resolved issues show `[x]` checkbox and resolution details
- Unresolved issues show `[ ]` checkbox and `_pending_` placeholder
- File is not committed to git (ephemeral review artifact)
- If issues.md already exists, `create` operation overwrites it
- Update operation is idempotent (updating same issue twice has same result)

## Integration

This command is called by `code-review-orchestrator-agent`:

```
# Create initial issues list from review findings
issueResult = invoke manage-issues-file({
  operation: "create",
  workDir: workDir,
  reviewPoints: review_findings
})

# Later, as fixes are applied...
updateResult = invoke manage-issues-file({
  operation: "update",
  workDir: workDir,
  issueId: "issue-1",
  resolved: true,
  resolution: "Applied fix in commit abc123"
})

# Check final status
statusResult = invoke manage-issues-file({
  operation: "read",
  workDir: workDir
})
```
