---
name: open-in-vscode
description: "Opens a file in VS Code. Use after writing a plan file so the developer sees it immediately."
user-invocable: false
---

# Open in VS Code

Opens a file in the user's VS Code editor using the `code` CLI.

## Usage

Call this skill with the absolute path to the file you want to open.

## Steps

1. Run the following command, substituting `<file_path>` with the absolute path to the file:

```bash
code "<file_path>"
```

2. If the `code` command is not found (exit code 127), report to the caller:
   > "VS Code CLI (`code`) is not available. The plan was written to `<file_path>`."
   Do not treat this as a fatal error — the file was already written successfully.

## Notes

- This skill does not open a new VS Code window if one is already running; it reuses the existing instance.
- Only use this after the file has been fully written to disk.
