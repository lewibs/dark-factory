---
name: declare-tools-in-agent-frontmatter
description: "Ensures every tool called in an agent's instruction body is also listed in the tools: YAML front-matter, because Claude Code uses that list as an access-control gate — omitting a tool there causes it to be silently unavailable at runtime."
user-invocable: false
---
## When to use

Use this whenever you create or modify an agent file (any `agents/**/*.md`) that calls a tool in its instruction body — especially native Claude Code tools like `PushNotification`, `WebSearch`, or custom tools. Also use it when debugging an agent that appears to skip a step silently (no error, but no effect).

## Steps

1. Open the agent file and read its YAML front-matter block (the section between the opening and closing `---` delimiters).
2. Identify the `tools:` field. If it is absent, add it.
3. Read the agent instruction body and collect every tool the agent is instructed to call (look for tool names like `PushNotification`, `Read`, `Bash`, `Agent`, `WebSearch`, etc.).
4. For each tool found in the body, confirm it is listed in the `tools:` front-matter field. If it is missing, add it to the comma-separated list.
5. Save the file.
6. Repeat for every agent file that was created or touched in the current task.

## Notes

- Claude Code grants an agent access to a tool **only** if that tool appears in the agent's `tools:` front-matter field. A tool referenced in the instruction body but absent from `tools:` is silently inaccessible — the agent will not error, it will simply skip or never reach that call.
- `PushNotification` is particularly easy to miss because it was added to agent bodies as a "notify before blocking on input" pattern after the initial `tools:` lists were written. Any future agent that adds this pattern must remember to add `PushNotification` to `tools:` as well.
- The `allowed-tools:` field (which restricts which sub-commands of `Bash` are permitted) is separate from `tools:` — both may need to be updated when adding new tool usage.
- A regression test (`tests/test_push_notification_declared.py`) exists in this repo that parses the YAML front-matter of all agent files and asserts `PushNotification` is present in `tools:` for every agent that references it in its body. Run this test after modifying agent files to catch omissions early.
