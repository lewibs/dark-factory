# Plan: Refactor Agent Output to Terse Structured JSON

## System Intent
update-documentation-agent and skill-update-agent currently generate multi-paragraph explanations during their execution. These verbose outputs consume output tokens (billed at full price even with prompt caching) and are rarely read. The refactor reduces output tokens by 40-70% by instructing both agents to return minimal JSON-style summaries listing only:
- Files written/updated (absolute paths)
- One-line summary of what was done

## Scope

### Files Modified
1. `agents/documentation/agents/update-documentation-agent.md`
2. `agents/skill-update/agents/skill-update-agent.md`

### Changes per Agent

#### update-documentation-agent
**Current behavior**: Writes multi-paragraph Phase descriptions, progress updates, checklist output during execution

**New behavior**:
- Suppress all prose output during Phase 1, 2, 3 execution
- At completion: return minimal structured output (JSON format or list)
- Output format: `{ "docsWritten": [...paths...], "summary": "one-liner" }`
- Example summary: "Updated 3 docs, created 1 new doc for auth-flow"

#### skill-update-agent  
**Current behavior**: Already has structured output defined (SkillUpdateOutput), but likely generates verbose prose during Steps 1-5

**New behavior**:
- Suppress all narrative output during Steps 1-5
- Return only: `{ "skillsWritten": [...paths...], "summary": "one-liner" }`
- Example summary: "Extracted 2 new patterns, created 1 skill file"

### Implementation Pattern
For each agent instruction file:
1. Keep the frontmatter (name, tools, model, etc.) unchanged
2. Keep the orchestration pseudocode structure but add instructions to suppress prose
3. Add explicit instruction: "Do NOT output progress messages, explanations, or prose — return only the final JSON summary"
4. Define concise output format upfront (before the orchestration section)
5. Update any completion/brain-patch sections to match the terse format

## Files Written
- `agents/documentation/agents/update-documentation-agent.md` — refactored instructions
- `agents/skill-update/agents/skill-update-agent.md` — refactored instructions

## Testing
After merging, verify in a test manufacture run:
1. Run /dark-factory:manufacture on a small feature task
2. Check that update-documentation-agent and skill-update-agent produce single-line JSON output
3. Verify output tokens are reduced (check Claude API usage logs if available)

