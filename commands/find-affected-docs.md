---
name: find-affected-docs
description: "Search docs/ directories for files affected by a feature plan. Match against system names, components, and sections mentioned in the plan."
user-invocable: false
---

# find-affected-docs

Identify which documentation files need updates based on a feature plan.

## Input

- `planPath` — absolute path to plan.md (string)
- `projectDir` — absolute path to project root (string)

## Output

### Found affected docs
```json
{
  "success": true,
  "affectedDocs": [
    {
      "path": "docs/docs/authentication.md",
      "reason": "Plan mentions 'OAuth' which is covered in authentication.md",
      "system": "authentication",
      "type": "docs"
    },
    {
      "path": "docs/plans/2024-03-15-oauth-feature.md",
      "reason": "Related plan for OAuth feature",
      "type": "plans"
    }
  ],
  "count": 2
}
```

### No docs affected
```json
{
  "success": true,
  "affectedDocs": [],
  "count": 0
}
```

### Error
```json
{
  "success": false,
  "reason": "Plan file not found"
}
```

## Algorithm

1. Read `planPath` to extract:
   - System Intent / primary system name
   - Component names mentioned in flows
   - Key terms (OAuth, payment, authentication, etc.)

2. Search `$projectDir/docs/docs/` for `.md` files:
   - Check filename against extracted system names (e.g., "oauth.md" for "OAuth")
   - Check file headers (## System, ## Components) against plan contents
   - Match key terms in file content

3. Search `$projectDir/docs/plans/` for `.md` files:
   - Check if plan title mentions same feature
   - Skip current plan file itself

4. Search `$projectDir/docs/bugs/` for `.md` files:
   - Check if resolved bug relates to plan's system

5. Return sorted list with match reasons

## Rules

- Match is case-insensitive
- Return results grouped by type (docs, plans, bugs)
- Include reason for each match (for validation)
- Exclude the plan file itself
- If no matches found, return empty array (not an error)
- Sort by relevance: docs first, then plans, then bugs

## Integration

This command is called by `update-documentation-agent` at the start:

```
affectedResult = invoke find-affected-docs({
  planPath: planPath,
  projectDir: projectDir
})

for each doc in affectedResult.affectedDocs:
  read doc.path
  update based on plan
  write updated content
```
