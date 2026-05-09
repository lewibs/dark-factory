---
name: mandatory-skill-invocation-phrasing
description: "Use this skill when writing agent instructions that must invoke another skill — advisory phrasing ('follow the skill') is silently skipped; only imperative phrasing with explicit enumeration of standards guarantees the skill is applied."
user-invocable: false
---
## When to use

Apply this rule whenever you write or update an agent instruction block that delegates work to a skill file. This covers:
- Agent phase instructions that reference a skill for diagram generation, formatting, or validation.
- Template sections that instruct downstream agents to follow a skill.
- Any prose instruction that says "follow", "use", "apply", or "refer to" a skill.

## Steps

1. **Identify all soft skill references in the instruction block.**
   - Soft references include: "follow the X skill", "use the X skill", "refer to X", "apply X standards".
   - These are silently skipped when an agent interprets them as optional guidance rather than required action.

2. **Replace each soft reference with an imperative block using MANDATORY.**
   - Before: `"Follow the create-mermaid-diagram skill when generating diagrams."`
   - After:
     ```
     **MANDATORY: First, read the skill at `skills/create-mermaid-diagram/SKILL.md`.**
     Apply all of its standards:
     - Node colors by file status (gray/yellow/red/green)
     - Edge labels on every arrow describing what flows
     - Black-box treatment for external services
     - Syntax validation with mmdc before finishing
     ```

3. **Enumerate the key standards inline, not just by reference.**
   - Listing the standards inside the instruction block ensures the agent applies them even if the skill read fails or is partial.
   - The enumerated list acts as a fallback and also makes compliance auditable.

4. **Add a Rules-section reinforcement for critical skills.**
   - If the skill is central to quality (e.g., diagram generation, output formatting), add a corresponding entry to the agent's `## Rules` section:
     ```
     - When generating <artifact>, you MUST read `skills/<slug>/SKILL.md` and follow all its standards before writing output.
     ```

5. **Do not rely on frontmatter `skills:` declarations alone.**
   - Frontmatter `skills:` is metadata consumed by the plugin loader. It does not cause the agent to read the skill at runtime.
   - Explicit imperative prose in the instruction body is the only mechanism that causes the agent to read and apply the skill.

## Notes

- **The symptom is silent non-compliance.** When an agent sees "follow the X skill" without an imperative read instruction, it may generate output from memory or prior context rather than reading the skill file. There is no error — the output simply does not conform to the skill's standards.
- **This is distinct from the `reference-skills-by-path` skill.** That skill addresses path vs slug resolution. This skill addresses advisory vs mandatory phrasing — the problem occurs even when the full path is present if the surrounding instruction is soft ("follow").
- **Canonical example:** `sub-planning-agent.md` listed `skills/create-mermaid-diagram/SKILL.md` in frontmatter and said "follow the create-mermaid-diagram skill" in the phase body. The agent generated diagrams without consistently applying node color rules or running mmdc validation. The fix added "MANDATORY: First, read the skill at `skills/create-mermaid-diagram/SKILL.md`" with an enumerated checklist of standards.
- **Use the word MANDATORY in bold** to distinguish required reads from informational references. Agents trained on this codebase treat bolded MANDATORY as a blocking gate, not an advisory hint.
