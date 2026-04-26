---
name: reference-skills-by-path
description: "Use this skill when writing or updating any agent, template, or skill file that needs to invoke another skill — always use an explicit path reference, never a short name."
user-invocable: false
---
## When to use

Any time you write or edit an agent (`.md` in `agents/`), a template, or a skill file that needs to tell a downstream agent to invoke a skill. This applies equally to new skill references and to updating existing ones.

## Steps

1. Identify every place the text says to "use the X skill" or "invoke the X skill" using only the short slug name.
2. Replace each short-name reference with the full explicit path form:
   - Pattern: `invoke the skill at \`skills/<slug>/SKILL.md\``
   - Example: replace "use the create-mermaid-diagram skill" with "invoke the skill at `skills/create-mermaid-diagram/SKILL.md`"
3. In agent frontmatter `skills:` declarations, the short slug is still correct (that field is metadata, not an invocation instruction). Do not change frontmatter slugs.
4. In prose instructions inside agent bodies, templates, and other skill files, always use the full backtick path form.
5. Verify every affected file contains the full path form before finishing.

## Notes

- Agents resolve skill references at runtime by reading the file at the stated path. A vague short name like "use the create-mermaid-diagram skill" does not give the agent a resolvable location, so the skill is silently skipped.
- The frontmatter `skills:` field is an exception — it is a metadata declaration consumed by the plugin loader, not a prose instruction to an agent, so short slugs remain correct there.
- When a new skill is added to `skills/`, audit all agents and templates that logically depend on that skill and ensure they reference it by path, not by name.
