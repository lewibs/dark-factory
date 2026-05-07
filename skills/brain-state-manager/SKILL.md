---
name: brain-state-manager
description: "Atomic operations for brain.json state management: create, read, patch, delete. Handles env var export and pointer file setup. Ensures consistent brain schema across all dark-factory runs."
user-invocable: false
---

# brain-state-manager

Manage the shared state file (brain.json) that orchestrates dark-factory work across multiple agents and phases.

## Operations

### create(taskDescription, taskName, workDir, projectDir, classification)

Creates a new brain.json in the work directory and sets up environment integration.

**Input**:
- `taskDescription` — user's task request (string)
- `taskName` — short slug for the feature (string, e.g., "add-oauth")
- `workDir` — absolute path to git worktree (string)
- `projectDir` — absolute path to original project root (string)
- `classification` — one of "feature" | "fix-flow" | "debugger" | "repair" (string)

**Output**:
```json
{
  "success": true,
  "brainPath": "/absolute/path/to/brain.json"
}
```

**Side effects**:
- Writes `$workDir/brain.json` with full schema
- Exports `DARK_FACTORY_WORK_DIR=$workDir` env var
- Writes `$workDir` to `/tmp/dark-factory-work-dir` pointer file
- All phases initialized with `*-running: false`, except `prep-complete: true`

**Schema (written to brain.json)**:
```json
{
  "taskDescription": "<taskDescription>",
  "taskName": "<taskName>",
  "workDir": "<workDir>",
  "projectDir": "<projectDir>",
  "classification": "<classification>",
  "planFilePath": null,
  "bugFiles": null,
  "prUrl": null,
  "docsWritten": null,
  "skillsWritten": null,
  "notes": [],
  "artifacts": {
    "created": [],
    "modified": []
  },
  "phases": {
    "prep-running": false,
    "prep-complete": true,
    "worker-running": false,
    "worker-complete": false,
    "review-running": false,
    "review-complete": false,
    "docs-running": false,
    "docs-complete": false,
    "skills-running": false,
    "skills-complete": false,
    "pr-running": false,
    "pr-complete": false,
    "cleanup-running": false,
    "cleanup-complete": false
  }
}
```

**Field descriptions for `notes` and `artifacts`**:
- `notes` — array of short handoff strings appended by agents as they complete (e.g., `"execution-agent: implemented auth-flow; changed files: src/auth.py, tests/test_auth.py"`). Read by the pre-hook and prepended prominently to each sub-agent's prompt so downstream agents know what prior agents did.
- `artifacts.created` — absolute paths of all new files created across this manufacture run. Populated by skeleton-agent, execution-agent, and update-documentation-agent.
- `artifacts.modified` — absolute paths of all existing files modified across this manufacture run. Populated by execution-agent, debugger-agent, and update-documentation-agent.

**Array merge behavior**: When agents write `notes`, `artifacts.created`, or `artifacts.modified` to `brain-patch.json`, the post-tool-use-hook concatenates these arrays rather than replacing them (unlike scalar fields which are overwritten). This ensures accumulation across multiple agent invocations.

### read(workDir, [path])

Reads the brain.json file (or a specific field within it).

**Input**:
- `workDir` — absolute path to git worktree (string)
- `path` — optional JSON path (e.g., "planFilePath", "phases.worker-complete") (string)

**Output** (no path specified):
```json
{
  "success": true,
  "data": { /* full brain.json contents */ }
}
```

**Output** (path specified):
```json
{
  "success": true,
  "data": "<field-value-at-path>"
}
```

**Error Output**:
```json
{
  "success": false,
  "reason": "brain.json not found in <workDir>"
}
```

### patch(workDir, fieldsObject)

Merges new fields into brain.json (shallow merge at top level, deep merge for nested objects).

**Input**:
- `workDir` — absolute path to git worktree (string)
- `fieldsObject` — JSON object with fields to merge (object)
  ```json
  {
    "planFilePath": "/path/to/plan.md",
    "phases": {
      "worker-complete": true
    }
  }
  ```

**Output**:
```json
{
  "success": true,
  "data": { /* updated brain.json after merge */ }
}
```

**Error Output**:
```json
{
  "success": false,
  "reason": "brain.json not found in <workDir>"
}
```

**Merge behavior**:
- For nested objects like `phases`, new fields are merged into the existing object (e.g., setting `phases.worker-complete: true` does not clear other phase flags)
- For array fields `notes`, `artifacts.created`, and `artifacts.modified`, new items are concatenated (appended) rather than replacing the existing array
- All other scalar/object fields use `jq -s '.[0] * .[1]'` shallow merge semantics (new value replaces old)

### delete(workDir)

Removes brain.json and pointer file.

**Input**:
- `workDir` — absolute path to git worktree (string)

**Output**:
```json
{
  "success": true,
  "deletedPath": "/absolute/path/to/brain.json"
}
```

**Side effects**:
- Removes `$workDir/brain.json`
- Removes `/tmp/dark-factory-work-dir` pointer file
- Clears `DARK_FACTORY_WORK_DIR` env var

## Rules

- `create` is called once per dark-factory run (by dark-factory-agent after prep)
- `read` is called after every sub-agent returns (to get output fields)
- `patch` is called by sub-agents via brain-patch.json (hooks do the merging; this operation is for direct access)
- `delete` is called before cleanup (mandatory — the cleanup script removes the entire worktree)
- Do NOT call `create` more than once per run; check if brain.json already exists first
- The pointer file `/tmp/dark-factory-work-dir` is a singleton (shared across all runs). It is used when the env var is not visible in a subprocess's environment.

## Environment Isolation Notes

- `DARK_FACTORY_WORK_DIR` must be `export`-ed so it propagates to child processes (hooks, sub-agents)
- In Claude Code Bash tool calls, env vars are reset between calls — the var only persists if explicitly exported in the same Bash call
- The pointer file `/tmp/dark-factory-work-dir` provides a fallback lookup mechanism for hooks that cannot see the env var
