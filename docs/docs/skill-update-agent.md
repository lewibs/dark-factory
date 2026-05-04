# skill-update-agent

**Role**: Post-implementation skill harvester and knowledge extractor.

**Model**: Sonnet (heavy reasoning for pattern detection and generalization).

**User-Invocable**: No (invoked by dark-factory-agent as non-fatal step).

## Overview

The skill-update-agent reviews completed work and harvests non-obvious, recurring patterns into reusable skill files. Skills are micro-tutorials capturing "how to do X in this codebase" — they accelerate future agents by codifying knowledge learned during manufacture runs. However, the agent is strict about quality: it only writes skills when a pattern is genuinely non-obvious AND likely to recur. Prefer returning an empty list over writing noise.

Unlike other agents, skill-update-agent is **non-fatal**: if it fails, dark-factory-agent logs a warning and continues to the PR step. This allows manufacturing to complete even if skill extraction fails.

## Input

- `planFilePath` (string, nullable) — Path to the approved and implemented plan file; may be null (e.g., for repair or debugger routes)
- `workDir` (string) — Absolute path to the isolated work directory
- `taskSummary` (string) — Brief human-readable description of what was accomplished

## Orchestration Flow (5 Steps)

### Step 1: Gather Context

1. **If planFilePath is not null**: reads plan to understand what flows were implemented and why
2. **Runs git commands** in workDir:
   - `git diff HEAD~1` or `git diff` to see code changes
   - `git log --oneline -5` to review recent commits
3. **Builds understanding** of what was done and what challenges were overcome

### Step 2: Identify Candidate Patterns

Scans the work for non-obvious patterns, workarounds, and discoveries.

**Detection signals**:
- Comments with "NOTE", "WORKAROUND", "HACK", "non-obvious"
- Repeated lookups in plan pseudocode (indicates something non-obvious)
- Deviations from standard patterns that were discovered and resolved
- Things the agent had to figure out that aren't documented elsewhere
- Tricky setup or configuration steps
- Interaction between systems that surprised the agent

**Examples of candidates**:
- "How to handle git conflicts when working in worktrees"
- "Pattern for calling Claude Code agents from bash"
- "When to use flow-state-manager vs brain-state-manager"
- "Proper error handling for non-fatal sub-agents"

**Examples to exclude** (too specific, not general):
- "How to fix the login bug in this specific codebase" (too specific to one bug)
- "The quirk of this particular service's API response" (specific data migration)
- "Workaround for this one edge case in our code" (not generalizable)

### Step 3: Recurrence Filter

For each candidate pattern, asks:

**"Is this specific to this one task, or would a future agent hit the same wall?"**

**Keep** (likely to recur):
- General patterns applicable to many tasks
- Setup/integration knowledge relevant to future work
- Common gotchas encountered
- Framework/tool knowledge that transfers across projects

**Discard** (task-specific):
- One-off data migrations
- Task-specific business logic fixes
- Project-specific quirks
- Edge cases unlikely to repeat

**Pragmatic principle**: Prefer returning `skillsWritten: []` (zero skills) if unsure. It's better to not write than to pollute the skills directory with noise.

### Step 4: Write/Update Skill Files

For each pattern passing the recurrence filter:

1. **Create kebab-case slug** (e.g., "handle-git-conflicts", "debug-cloudbuild-logs")
2. **Determine path**: `skills/<slug>/SKILL.md` (relative to workDir)
3. **Check if exists**:
   - **If already exists**: read existing skill, merge new knowledge, write updated file; record `action: "updated"`
   - **If new**: write new SKILL.md using template below; record `action: "created"`

### Step 5: Return Result

Returns:
```json
{
  "skillsWritten": [
    { "path": "skills/handle-git-conflicts/SKILL.md", "action": "created" },
    { "path": "skills/debug-cloudbuild/SKILL.md", "action": "updated" }
  ]
}
```

**If no patterns qualified**: returns `{ skillsWritten: [] }` (empty list).

## Skill Template

When creating a new skill file, use this format:

```markdown
---
name: <kebab-case-slug>
description: "<one sentence: what this skill does and when to use it>"
user-invocable: false
---

## When to use

<Condition or situation that triggers the need for this skill>

Examples:
- "When working with git worktrees in dark-factory"
- "When a Claude Code pre-hook needs to intercept an Agent tool call"

## Steps

<Numbered steps describing how to do the thing>

1. First step
2. Second step
3. ...

## Notes

<Any caveats, gotchas, or edge cases>

Examples:
- "Remember to handle the null case in step 2"
- "Only use this for X; don't use for Y"
- "This pattern requires Z to be installed"
```

## Key Design Rules

1. **Only write for non-obvious, recurring patterns** — Filter aggressively; prefer empty list over noise
2. **Don't modify files outside skills/** — Leave agent files, plans, and code untouched
3. **Merge when updating** — Preserve existing skill content and add new knowledge; don't overwrite
4. **Non-fatal failures** — If plan file can't be read or git fails, report error but don't block dark-factory-agent
5. **Write brain-patch only if skills written** — If `skillsWritten` is empty, omit brain-patch entirely

## Brain Patch Output

If any skills were written or updated, write `$DARK_FACTORY_WORK_DIR/brain-patch.json`:
```json
{
  "skillsWritten": [
    "skills/handle-git-conflicts/SKILL.md",
    "skills/debug-cloudbuild/SKILL.md"
  ]
}
```

**Rules**:
- Only write brain-patch if `skillsWritten` is non-empty
- Skip writing silently if `DARK_FACTORY_WORK_DIR` is unset
- Do not read brain.json directly (context is injected by pre-hook)
- Do not write brain.json (only write brain-patch.json)

## Dependencies

- **No skills or sub-agents required**
- **Templates**: skill-template (used when creating new skills)

## Tools

- Read, Write, Edit, Bash (for git commands)

## Integration with dark-factory-agent

1. Invoked after update-documentation-agent completes
2. **Non-fatal**: if it returns error or times out, dark-factory-agent logs warning and continues to PR
3. No blocking — always proceeds to pr-agent regardless of skill-update result
4. Output (skillsWritten) is used by dark-factory-agent for metrics and attribution

## Error Handling

- If plan file is unreadable: reports error (non-fatal, caller continues)
- If git commands fail: reports error (non-fatal, caller continues)
- If skill template doesn't exist: reports error (non-fatal, caller continues)
- If workDir doesn't exist: reports error (non-fatal, caller continues)

## Use Case Examples

**Good candidates**:
- "How to parse Claude Code's pre-hook JSON format"
- "Pattern for delegating to flow-state-manager"
- "Debugging checklist for state-dependent bugs"
- "How to write agent tests with dark-factory"

**Poor candidates**:
- "The specific bug we fixed in this one task"
- "This project's particular API quirk"
- "Workaround for this vendor's rate limit"
