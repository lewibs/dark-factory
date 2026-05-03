---
name: render-plan-section
description: "Extract and render a named section from a plan.md file, with fallback to raw markdown if rendering fails."
user-invocable: false
---

# render-plan-section

Extract a named markdown section from a plan file and render it for display.

## Input

- `planPath` — absolute path to plan.md file (string)
- `sectionName` — the section to extract (string, e.g., "## System Intent", "### Flow: payment-processing")

## Output

Returns a JSON object:

```json
{
  "success": true,
  "rendered": "formatted content here",
  "fallback": false
}
```

Or with fallback:

```json
{
  "success": true,
  "rendered": "raw markdown content",
  "fallback": true
}
```

Or error:

```json
{
  "success": false,
  "reason": "Section not found in plan file"
}
```

## Algorithm

1. Read `planPath` from disk
2. Search for `sectionName` (exact match, line by line)
3. Extract all lines from `sectionName` until the next same-level heading (e.g., if section is `## System Intent`, extract until the next `##` heading)
4. Pass extracted content to `${CLAUDE_PLUGIN_ROOT}/scripts/render_section.py`
5. If render succeeds (exit code 0): return rendered output with `fallback: false`
6. If render fails: return raw extracted content with `fallback: true`
7. If section not found: return error

## Examples

### Extract "## System Intent"

**Input**:
```json
{
  "planPath": "/home/user/work/plan.md",
  "sectionName": "## System Intent"
}
```

**Output**:
```json
{
  "success": true,
  "rendered": "Formatted HTML or markdown...",
  "fallback": false
}
```

### Extract "### Flow: authentication"

**Input**:
```json
{
  "planPath": "/home/user/work/plan.md",
  "sectionName": "### Flow: authentication"
}
```

**Output**:
```json
{
  "success": true,
  "rendered": "Flow details...",
  "fallback": false
}
```

## Rules

- Section names must match exactly (case-sensitive)
- Extraction includes the heading line itself
- Stops at the next heading of equal or lesser depth (e.g., `## X` stops at the next `##` or `#` heading)
- If the section is the last section in the file, extract to EOF
- Rendering failures fall back to raw markdown (non-fatal)
