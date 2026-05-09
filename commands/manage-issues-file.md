---
name: manage-issues-file
description: "Create, read, and delete the issues.md file during code review. The file uses a freeform markdown checklist format where each issue is a single line appended by review agents."
user-invocable: false
---

# manage-issues-file

Manage the issues.md file that tracks code review findings and their resolution status.

The file uses a freeform markdown checklist format. Each issue line is written by the review agents in this form:

```
- [ ] [high-level] <description> (<filePath>)
- [ ] [low-level] <description> (<filePath>)
```

Resolved issues have the checkbox checked:

```
- [x] [high-level] <description> (<filePath>)
- [x] [low-level] <description> (<filePath>)
```

## Input

All operations use `issuesFilePath` (absolute path) to locate the issues file.

### Operation: create

Create a new empty issues.md file. Any existing content is overwritten.

**Input**:
```json
{
  "operation": "create",
  "issuesFilePath": "/absolute/path/to/issues.md"
}
```

**Output**:
```json
{
  "success": true,
  "path": "/absolute/path/to/issues.md"
}
```

**How to execute**: Write an empty string (or a header comment) to `issuesFilePath`. Create parent directories if needed.

### Operation: read

Read the current issues.md file and count checked/unchecked items.

**Input**:
```json
{
  "operation": "read",
  "issuesFilePath": "/absolute/path/to/issues.md"
}
```

**Output**:
```json
{
  "success": true,
  "unresolvedCount": 2,
  "resolvedCount": 1,
  "totalCount": 3
}
```

**How to execute**: Read `issuesFilePath`, count lines matching `- [ ]` (unresolved) and `- [x]` (resolved).

### Operation: delete

Delete the issues.md file.

**Input**:
```json
{
  "operation": "delete",
  "issuesFilePath": "/absolute/path/to/issues.md"
}
```

**Output**:
```json
{
  "success": true
}
```

**How to execute**: Delete the file at `issuesFilePath`. If it does not exist, treat as success.

## Issues.md Format

The issues.md file is a flat checklist of markdown lines:

```markdown
- [ ] [high-level] Missing null check on user object (/path/to/auth/login.ts)
- [x] [low-level] Unused import statement (/path/to/api/auth.ts)
- [ ] [low-level] Color contrast accessibility issue (/path/to/styles/login.css)
```

## Rules

- The file format is a plain markdown checklist — one issue per line
- Resolved issues show `[x]`; unresolved issues show `[ ]`
- Review agents append lines directly to this file; the command does not parse or rewrite appended lines
- `create` operation always writes an empty file (clears any prior content)
- `delete` operation removes the file when code review is complete
- File is not committed to git (ephemeral review artifact)

## Integration

This command is called by `code-review-orchestrator-agent`:

```
# Create empty issues list before spawning reviewers
issueResult = invoke manage-issues-file({
  operation: "create",
  issuesFilePath: issuesFilePath
})

# After resolver loop, check final status
statusResult = invoke manage-issues-file({
  operation: "read",
  issuesFilePath: issuesFilePath
})

# On successful completion, delete the file
invoke manage-issues-file({
  operation: "delete",
  issuesFilePath: issuesFilePath
})
```
