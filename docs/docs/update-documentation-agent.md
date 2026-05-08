# update-documentation-agent

**Role**: Post-implementation documentation updater.

**Model**: Sonnet (heavy reasoning for documentation analysis and writing).

**Prompt Caching**: Yes — set in YAML frontmatter. Claude Code applies prompt caching when spawning this agent, reducing system prompt token costs.

**User-Invocable**: No (invoked by dark-factory-agent after code review).

**Output Style**: Terse JSON — no progress prose.

## Overview

The update-documentation-agent automatically updates project documentation after a plan has been implemented and reviewed. It reads the approved plan, identifies all created and modified flows/services/components, locates affected documentation files, and updates them to reflect the implementation. It also creates new doc files for any flows that don't yet have documentation.

The agent is a critical part of keeping documentation in sync with code — it ensures that every implemented flow/service has current, accurate documentation.

Returns minimal structured output listing files written and a one-line summary (e.g., "Updated 2 docs for auth-flow and caching; created 1 new doc for metrics").

## Input

- `planFilePath` (string, nullable) — Absolute path to the implemented and approved plan file
- `workDir` (string, optional) — Absolute path to the target worktree. When provided, takes priority over the env var and pointer-file fallbacks. If none of the three sources resolves to a value, the agent returns a hard-stop error.
- If `planFilePath` is not provided: sends PushNotification ("Input Required"), awaits AskUserQuestion for path or skip option

## Output Format

Returns terse structured output as the final message:

```json
{
  "docsWritten": ["<absolute-path-1>", "<absolute-path-2>"],
  "summary": "<one-line description of work>"
}
```

**Example**: `{ "docsWritten": ["/path/docs/auth-flow.md"], "summary": "Updated auth-flow docs, created new integration example" }`

**Key behavior**: Executes silently (no progress messages, phase descriptions, or narrative prose) and returns only this minimal JSON summary.

## Orchestration Flow (3 Phases)

### WORK_DIR Resolution

Before any file write, the agent resolves its working directory. Each source is checked in order and the first non-empty value wins:

```
WORK_DIR = workDir argument (if provided in the invocation and non-empty)
if WORK_DIR is still empty: WORK_DIR = $DARK_FACTORY_WORK_DIR (env var)
if WORK_DIR is still empty: WORK_DIR = contents of /tmp/dark-factory-work-dir (if the file exists)
if WORK_DIR is still empty: STOP — return error JSON:
  {"error": "WORK_DIR could not be resolved. Cannot write docs without a target directory. Pass workDir explicitly."}
```

The agent does **not** fall back to `"."` (CWD). Writing to the current working directory would silently contaminate the main project repo when the agent runs outside an isolated worktree. If WORK_DIR cannot be resolved the agent halts immediately and surfaces the error to the caller.

All file paths produced by the agent are prefixed with `$WORK_DIR/`. This ensures writes always land in the isolated feature worktree.

### Phase 1: Identify Flows

1. Reads the plan file at `planFilePath`
2. Extracts every flow, service, or component that was created or modified
3. Builds `$WORK_DIR/tmp/update-docs-flows.md` checklist (internal only — not output)

### Phase 2: Identify Affected Docs

1. Invokes `find-affected-docs` command with flow names from Phase 1
2. Command searches `docs/docs/` for existing files that mention the flows
3. Appends to `$WORK_DIR/tmp/update-docs-flows.md` (internal only — not output); entries use absolute paths (`$WORK_DIR/docs/docs/<file>.md`)

### Phase 3: Update Docs

For each item in Phase 2 checklist:

**For existing doc files**:
1. Opens the doc file (at its absolute `$WORK_DIR`-prefixed path)
2. Identifies sections affected by implementation changes
3. **Deletes removed behavior** — Removes descriptions of features that were deleted or refactored out
4. **Updates modified** — Changes sections to reflect implementation details that changed
5. **Adds new** — Inserts descriptions of new flows, endpoints, methods, or behaviors added by the implementation

**For new flows**:
1. Creates `$WORK_DIR/docs/docs/<flow-name>.md` as a new file
2. Uses the `documentation` skill to generate comprehensive documentation
3. Includes: purpose, inputs, outputs, workflow, error handling, dependencies

Collects absolute paths of all files written/updated.

## Completion

Returns terse JSON with files updated and one-line summary.

Writes `$WORK_DIR/brain-patch.json`:
```json
{
  "docsWritten": ["<absolute-path-1>", "<absolute-path-2>"],
  "summary": "<one-liner>"
}
```

**WORK_DIR resolution**: check `workDir` argument first; else use `$DARK_FACTORY_WORK_DIR`; else read `/tmp/dark-factory-work-dir`; if all three are empty, halt with error — no CWD fallback. The same resolution applies to all file writes throughout the agent, not just brain-patch.json.

## Key Design Rules

1. **Read plan before touching docs** — Understand all changes before updating
2. **Delete removed behavior** — Don't leave documentation for features that no longer exist
3. **Update, don't rewrite** — For existing docs, edit sections; don't rebuild the whole file
4. **Create new docs for new flows** — Don't assume documentation exists for new flows
5. **Use documentation skill** — Delegate doc generation for new flows to the skill
6. **Track all changes** — Write brain-patch.json with paths to every file touched
7. **Work silently** — Execute all phases without output prose; return only final JSON summary
8. **Always resolve WORK_DIR before writing** — All file paths (tmp checklist, docs/docs/, brain-patch.json) must be prefixed with `$WORK_DIR/`. Resolve WORK_DIR at the start: check `workDir` argument, then `$DARK_FACTORY_WORK_DIR`, then `/tmp/dark-factory-work-dir`. If none resolve, halt with an error — never fall back to CWD or bare relative paths.

## Dependencies

- **Commands**: find-affected-docs (identifies which existing docs mention which flows)
- **Skills**: documentation (generates new flow documentation)

## Tools

- Read, Bash, Write, Edit, PushNotification, AskUserQuestion, Command

## Artifacts Produced

- `$WORK_DIR/tmp/update-docs-flows.md` — Checklist of flows and affected docs (internal; not output)
- `$WORK_DIR/docs/docs/<flow-name>.md` — New doc files created for flows without docs
- Modified existing doc files in `$WORK_DIR/docs/docs/`
- `$WORK_DIR/brain-patch.json` — Paths of all files written/updated and one-line summary

## SubagentStop Hook

The agent declares a `SubagentStop` hook in its YAML frontmatter:

```yaml
SubagentStop: "${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/commit-on-subagent-stop.sh"
```

When the agent finishes, this hook fires and commits all staged changes in the feature worktree with commit message `"docs: update documentation"`. This ensures documentation updates are committed as a discrete, ordered step in the manufacture commit sequence.

## Integration with dark-factory-agent

1. Called after code-review-orchestrator-agent completes
2. Must complete before skill-update-agent
3. If returns error: dark-factory-agent halts, cleans up, reports failure
4. If succeeds: dark-factory-agent continues to skill-update and PR
5. Output (docsWritten) is used by dark-factory-agent for metrics and attribution

## Error Handling

- If WORK_DIR cannot be resolved (no `workDir` arg, env var unset, pointer file absent): returns `{"error": "WORK_DIR could not be resolved..."}` and halts — no CWD fallback
- If plan file not provided: requests via AskUserQuestion; halts if user skips
- If plan file unreadable: reports error and halts
- If find-affected-docs command fails: reports error and halts
- If doc writing fails: reports which file failed and halts
