# Skills

This directory contains skills that teach the agent how to handle specific tasks or workflows.

## What is a Skill?

A skill is a folder containing:

- **SKILL.md (required):** Instructions in Markdown with YAML frontmatter.
- **scripts/ (optional):** Executable code.
- **references/ (optional):** Documentation.
- **assets/ (optional):** Templates, etc.

## Creating a New Skill

1.  **Create a folder** with a kebab-case name (e.g., `my-new-skill`).
2.  **Create SKILL.md** inside that folder.
3.  **Add YAML Frontmatter**:

    ```yaml
    ---
    name: my-new-skill
    description: A description of what the skill does and when to use it (trigger phrases).
    ---
    ```

    - `name`: Must match the folder name exactly.
    - `description`: Required. identifying when to use the skill. No XML tags allowed.

4.  **Write Instructions**: Add the skill content below the frontmatter.

## Frontmatter Requirements

- **name**: Required. Kebab-case, matching folder name.
- **description**: Required. Under 1024 characters.

## Security

- Do NOT use "claude" or "anthropic" in skill names.
