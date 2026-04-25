---
name: create-new-skill
description: Create or update an agent skill using Claude Skills conventions. Use when adding a skill folder, writing SKILL.md frontmatter/content, configuring invocation controls, or organizing supporting skill files.
---

## Required

Use this skill whenever you create or update files under `.agent/skills/<skill-name>/`.

1. Create or update `.agent/skills/<skill-name>/SKILL.md` (folder name in lowercase kebab-case).
2. Write YAML frontmatter using only Claude-supported fields:
   - `name` (optional): lowercase letters, numbers, hyphens, max 64 chars. If omitted, directory name is used.
   - `description` (recommended): include what the skill does and when to use it with natural user phrasing.
   - Optional behavior fields: `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `context`, `agent`, `hooks`.
3. Write the markdown body with operational instructions Claude should follow when the skill is invoked.
4. Pick invocation mode based on skill type:
   - Reference skill: usually auto-invocable by Claude.
   - Task skill: often set `disable-model-invocation: true` to require explicit `/skill-name`.
5. Add supporting files when helpful and reference them from `SKILL.md`:
   - Detailed docs/examples in same folder or `references/`.
   - Executable helpers in `scripts/`.
   - Reusable output templates/assets in `assets/`.
6. Include argument placeholders when needed:
   - `$ARGUMENTS`, `$ARGUMENTS[N]`, or `$N`.
7. Validate behavior by testing both:
   - Natural language request that should auto-trigger.
   - Direct invocation via `/skill-name`.

## Context

Build skills for high trigger accuracy and low context load.

- `SKILL.md` is required; supporting files are optional.
- Keep `SKILL.md` under 500 lines; move details to supporting files.
- Descriptions are key for auto-triggering; include keywords users naturally say.
- For side effects, default to manual invocation with `disable-model-invocation: true`.
- `user-invocable: false` hides slash menu usage but still allows Claude invocation.

## Troubleshooting

- Skill not triggering:
  1. Ensure description contains likely user keywords.
  2. Confirm skill appears in available skills listing.
  3. Rephrase prompt closer to description language.
  4. Invoke directly with `/skill-name`.
- Skill triggers too often:
  1. Narrow description scope.
  2. Set `disable-model-invocation: true` for manual-only usage.
- Not all skills visible:
  1. Check context budget (`/context`) for excluded skills (2% of total window, minimum 16k tokens).
  2. Reduce description verbosity or skill count.

## Template

`references/skill-template.md` is an optional starting scaffold aligned to Claude frontmatter and invocation patterns.
