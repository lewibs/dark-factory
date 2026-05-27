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

6. If the command invokes a shell script (common pattern: the command delegates to `scripts/<name>.sh`), ensure that script actually exists. A missing script causes the command to silently fail at runtime — there is no registration-time error.

7. Add (or update) the command's row in the README command table. The README table is not auto-generated; it must be kept in sync manually. Rows that exist in the table without a corresponding `commands/<name>.md` file are "ghost" entries and confuse users.

## Notes

- The silent-ignore behavior is the key gotcha: if you put a command file in `agents/commands/` (a directory used for orchestrator instruction files), it will appear to be in the right place but will never be registered as a slash-command. There is no error or warning.
- `agents/commands/` is a convention for storing the detailed orchestrator instructions that a command delegates to — it is NOT where the command entry-point lives.
- The distinction: `commands/<name>.md` = the registered slash-command entry-point; `agents/commands/<name>-orchestrator.md` = the detailed instructions the entry-point delegates to.

## Deprecating and removing a command

Marking a command file's body as `[DEPRECATED]` or adding deprecation prose to the description does **not** remove the slash-command from the plugin. The file's presence in `commands/` is all that matters — the plugin loader registers every `.md` file it finds there regardless of content.

To fully retire a command:
1. Delete the file: `rm commands/<name>.md`
2. Remove its row from the README command table.
3. Reinstall the plugin with `/dark-factory:install` to deregister the command.

Do NOT leave the file in place with a deprecation notice if the goal is to stop the command from appearing — the file must be deleted.
