# Mermaid Diagram Skill Not Being Applied During Planning

## Metadata

- Date: `2026-05-09`
- Status: `fixed`
- Severity: `medium`
- Related issue/ticket: `N/A`
- Owner: `lewibs`

## About

**Overview**:
- The `create-mermaid-diagram` skill was declared in the frontmatter of sub-planning-agent.md but was not explicitly required to be read and followed during diagram generation.
- Instead, sub-planning-agent would generate Mermaid diagram syntax directly based on the inline reference "follow the skill" without explicitly reading the skill file.
- This created a risk that diagram standards (node colors, edge labels, validation) would not be consistently applied.

**Root Cause**:
- sub-planning-agent.md listed `skills/create-mermaid-diagram/SKILL.md` in its YAML frontmatter (line 7)
- The mermaid phase documentation (line 62) said "follow the `create-mermaid-diagram` skill" but did not explicitly require the agent to read and reference it
- The instructions were vague ("follow") rather than imperative ("read the skill at skills/create-mermaid-diagram/SKILL.md and apply these standards")
- This allowed the agent to apply standards inconsistently or incompletely

**Expected Behavior**:
- When sub-planning-agent needs to generate or update a Mermaid diagram, it must explicitly read the `create-mermaid-diagram` skill
- The agent must apply all standards from the skill:
  - Node colors: Gray (unchanged), Yellow (updated), Red (deleted), Green (created)
  - Edge labels for all data flow
  - Black-box treatment for external services
  - Syntax validation with mmdc
- sub-planning-agent should focus on planning logic while delegating diagram standards to the skill

**System Context**:
- File: `agents/featurework/planning/agents/sub-planning-agent.md`
- Phase affected: `mermaid` (phase 2 of feature planning)
- Related skill: `skills/create-mermaid-diagram/SKILL.md`
- Planning-agent: orchestrator that invokes sub-planning-agent for each phase

## Reproduction Details

**Before Fix**:
1. feature-agent invokes planning-agent with `phase: "mermaid"`
2. planning-agent delegates to sub-planning-agent
3. sub-planning-agent receives `feedback` (user changes to diagram)
4. sub-planning-agent reads instructions saying "follow the skill" but doesn't explicitly read the skill file
5. sub-planning-agent may apply standards inconsistently or incompletely
6. No guarantee that node colors, edge labels, and validation match skill requirements

**After Fix**:
1. feature-agent invokes planning-agent with `phase: "mermaid"`
2. planning-agent delegates to sub-planning-agent
3. sub-planning-agent receives `feedback`
4. Sub-planning-agent receives explicit instruction: "**MANDATORY: First, read the `create-mermaid-diagram` skill at `skills/create-mermaid-diagram/SKILL.md`**"
5. Sub-planning-agent reads the skill and explicitly applies all standards from it:
   - Node colors by file status
   - Edge labels for data flow
   - Black-box services
   - mmdc validation
6. sub-planning-agent writes updated plan file with diagram conforming to skill standards
7. sub-planning-agent runs mermaid_to_image.py and returns URL

## Verification

- [x] Verified skill exists at `skills/create-mermaid-diagram/SKILL.md`
- [x] Verified skill was declared in sub-planning-agent frontmatter (line 7)
- [x] Verified instructions were vague ("follow") rather than imperative
- [x] Updated sub-planning-agent.md mermaid phase instructions
- [x] Made explicit: "MANDATORY: First, read the `create-mermaid-diagram` skill"
- [x] Listed all required standards that must be applied
- [x] Updated rules section to reinforce skill compliance

## Changes Made

**File: `/home/lewibs/github/dark_factory/dark_factory/agents/featurework/planning/agents/sub-planning-agent.md`**

1. **Phase: mermaid section (lines 57-82)**:
   - Added explicit step 2a: "**MANDATORY: First, read the `create-mermaid-diagram` skill**"
   - Listed all required standards from the skill (node colors, edge labels, services, validation)
   - Changed step 2b to reference "standards from the skill"

2. **Rules section (line 119-120)**:
   - Updated mermaid rule to emphasize: "When feedback is not 'none', you MUST read the `create-mermaid-diagram` skill and follow all its standards"

These changes ensure the agent doesn't just reference the skill but explicitly reads and applies it.

## Audit Log

| ID | Action | Note | Context |
| --- | --- | --- | --- |
| 1 | Create audit log | Initialize bug investigation | User reported skill not being used |
| 2 | Verify skill exists | Read skills/create-mermaid-diagram/SKILL.md | Exists, properly documented |
| 3 | Check sub-planning-agent frontmatter | Verified skill listed in frontmatter line 7 | Present as dependency |
| 4 | Analyze mermaid phase logic | Read lines 57-82 of sub-planning-agent.md | Instructions say "follow" but not explicit |
| 5 | Root cause identified | Vague instruction ("follow") vs imperative ("read and apply") | Confirmed |
| 6 | Fix applied | Added explicit "MANDATORY: First, read..." instruction | Updated sub-planning-agent.md |
| 7 | List required standards | Added detailed list of standards from skill | Now explicit in instructions |
| 8 | Update rules section | Added enforcement text for mermaid rule | Reinforces skill compliance |
| 9 | Verify no regressions | Checked that fix doesn't change logic, only clarity | Only documentation clarity improved |

## Notes for PR

**Root Cause Analysis**:
The skill was declared as a dependency but the instructions to use it were vague. A Sonnet agent reading "follow the create-mermaid-diagram skill" might interpret it as just general guidance rather than a mandatory requirement to explicitly read and apply that specific skill file.

**Fix Applied**:
Changed the mermaid phase instructions to explicitly require reading the skill and listing all the standards that must be applied. The word "MANDATORY" makes it clear this is not optional.

**Testing**:
No behavioral regression — the fix is purely instructional clarity. Agents will now explicitly read the skill (which they always could do) rather than implicitly hoping they'd follow it.

## References

- Skill: `skills/create-mermaid-diagram/SKILL.md` — contains diagram standards
- Plan template: `agents/featurework/planning/templates/plan-template.md` — references the skill
- Feature-agent: `agents/featurework/agents/feature-agent.md` — invokes planning-agent
- Planning-agent: `agents/featurework/planning/agents/planning-agent.md` — orchestrator
