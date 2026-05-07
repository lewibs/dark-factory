---
name: plugin-command-must-be-in-commands-dir
description: "Plugin slash-commands must be placed directly in the commands/ directory (as declared by plugin.json), not in agents/commands/ or any other subdirectory, or the plugin loader will silently ignore them."
user-invocable: false
---
## When to use

Any time you create, move, or rename a slash-command (i.e. a file that should be accessible as `/dark-factory:<name>`) for the dark-factory plugin.

## Steps

1. Confirm the commands directory declared in `.claude-plugin/plugin.json`:
   ```json
   { "commands": "./commands/" }
   ```
   This means `commands/` at the plugin root is the only directory the loader scans.

2. Place the command file at:
   ```
   commands/<name>.md
   ```
   For example, a command intended to be invoked as `/dark-factory:investigation` must live at `commands/investigation.md`.

3. Do NOT place command files in `agents/commands/` or any other location. Files outside `commands/` are silently skipped by the plugin loader — no error is raised.

4. The command file only needs a YAML frontmatter `description:` field and the body can delegate to an agent orchestrator:
   ```markdown
   ---
   description: "Short description of what this command does."
   ---

   Follow the instructions in `agents/commands/<orchestrator>.md` exactly.
   ```

5. After adding or moving a command file, reinstall the plugin with `/dark-factory:install` to pick up the change.

## Notes

- The silent-ignore behavior is the key gotcha: if you put a command file in `agents/commands/` (a directory used for orchestrator instruction files), it will appear to be in the right place but will never be registered as a slash-command. There is no error or warning.
- `agents/commands/` is a convention for storing the detailed orchestrator instructions that a command delegates to — it is NOT where the command entry-point lives.
- The distinction: `commands/<name>.md` = the registered slash-command entry-point; `agents/commands/<name>-orchestrator.md` = the detailed instructions the entry-point delegates to.
