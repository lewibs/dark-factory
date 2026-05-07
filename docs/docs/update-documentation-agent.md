# update-documentation-agent

**Role**: Post-implementation documentation updater.

**Model**: Sonnet (heavy reasoning for documentation analysis and writing).

**Prompt Caching**: Yes — `cache-control: ephemeral` is set in YAML frontmatter. Claude Code applies prompt caching when spawning this agent, reducing system prompt token costs by ~90% for repeated invocations.

**User-Invocable**: No (invoked by dark-factory-agent after code review).

## Overview

The update-documentation-agent automatically updates project documentation after a plan has been implemented and reviewed. It reads the approved plan, identifies all created and modified flows/services/components, locates affected documentation files, and updates them to reflect the implementation. It also creates new doc files for any flows that don't yet have documentation.

The agent is a critical part of keeping documentation in sync with code — it ensures that every implemented flow/service has current, accurate documentation.

## Input

- `planFilePath` (string, nullable) — Absolute path to the implemented and approved plan file
- If not provided: sends PushNotification ("Input Required"), awaits AskUserQuestion for path or skip option

## Orchestration Flow (3 Phases)

### Phase 1: Identify Flows

1. Reads the plan file at `planFilePath`
2. Extracts every flow, service, or component that was created or modified
3. Builds `tmp/update-docs-flows.md` checklist:
   ```markdown
   # Flows Checklist
   - [ ] <flow-name> — created/modified
   - [ ] <service-name> — created/modified
   - [ ] <component-name> — created/modified
   ```

### Phase 2: Identify Affected Docs

1. Invokes `find-affected-docs` command with flow names from Phase 1
2. Command searches `docs/docs/` for existing files that mention the flows
3. Appends to `tmp/update-docs-flows.md`:
   ```markdown
   # Affected Docs Checklist
   - [ ] docs/docs/existing-flow.md — touches <flow-name>
   - [ ] docs/docs/service-integration.md — touches <flow-name>
   - [ ] NEW — <new-flow-name> has no existing doc
   - [ ] NEW — <new-service-name> has no existing doc
   ```

### Phase 3: Update Docs

For each item in Phase 2 checklist:

**For existing doc files**:
1. Opens the doc file
2. Identifies sections affected by implementation changes
3. **Deletes removed behavior** — Removes descriptions of features that were deleted or refactored out
4. **Updates modified** — Changes sections to reflect implementation details that changed
5. **Adds new** — Inserts descriptions of new flows, endpoints, methods, or behaviors added by the implementation
6. Marks checklist item `[x]` when complete

**For new flows** (marked as "NEW"):
1. Creates `docs/docs/<flow-name>.md` as a new file
2. Uses the `documentation` skill to generate comprehensive documentation
3. Includes: purpose, inputs, outputs, workflow, error handling, dependencies
4. Marks checklist item `[x]` when complete

## Completion

After all docs are updated or created, resolves WORK_DIR and writes `$WORK_DIR/brain-patch.json`:
```json
{
  "docsWritten": [
    "/absolute/path/to/docs/docs/flow-1.md",
    "/absolute/path/to/docs/docs/flow-2.md",
    "/absolute/path/to/docs/docs/service.md"
  ]
}
```

**WORK_DIR resolution**: use `$DARK_FACTORY_WORK_DIR` if set; else read contents of `/tmp/dark-factory-work-dir` (if file exists); skip silently if both are empty.

## Key Design Rules

1. **Read plan before touching docs** — Understand all changes before updating
2. **Delete removed behavior** — Don't leave documentation for features that no longer exist
3. **Update, don't rewrite** — For existing docs, edit sections; don't rebuild the whole file
4. **Create new docs for new flows** — Don't assume documentation exists for new flows
5. **Use documentation skill** — Delegate doc generation for new flows to the skill
6. **Track all changes** — Write brain-patch.json with paths to every file touched
7. **Resolve WORK_DIR via pointer file fallback** — Check `$DARK_FACTORY_WORK_DIR`; if unset, read `/tmp/dark-factory-work-dir`; skip brain-patch silently if both empty

## Dependencies

- **Commands**: find-affected-docs (identifies which existing docs mention which flows)
- **Skills**: documentation (generates new flow documentation)

## Tools

- Read, Bash, Write, Edit, PushNotification, AskUserQuestion, Command

## Artifacts Produced

- `tmp/update-docs-flows.md` — Checklist of flows and affected docs
- `docs/docs/<flow-name>.md` — New doc files created for flows without docs
- Modified existing doc files in `docs/docs/`
- `$DARK_FACTORY_WORK_DIR/brain-patch.json` — Metadata of all files written/updated

## Integration with dark-factory-agent

1. Called after code-review-orchestrator-agent completes
2. Must complete before skill-update-agent
3. If returns error: dark-factory-agent halts, cleans up, reports failure
4. If succeeds: dark-factory-agent continues to skill-update and PR
5. Output (docsWritten) is used by dark-factory-agent for metrics and attribution

## Error Handling

- If plan file not provided: requests via AskUserQuestion; halts if user skips
- If plan file unreadable: reports error and halts
- If find-affected-docs command fails: reports error and halts
- If doc writing fails: reports which file failed and halts
