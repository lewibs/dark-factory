---
name: command-must-invoke-agent-by-name
description: "Plugin command files (commands/*.md) must invoke agents via the Agent tool by name, not by referencing an agent .md file path inline, because path-based references fail in nested Claude sessions where CWD is not the plugin root."
user-invocable: false
---
## When to use

Any time you create or modify a file in `commands/` that is meant to delegate to
an agent. Also use when debugging a command that works when invoked directly but
silently falls through or executes inline logic in a nested session.

## Steps

1. Open the command file (e.g., `commands/manufacture.md`).

2. In the YAML frontmatter, declare `tools: Agent`:
   ```markdown
   ---
   description: "Short description."
   tools: Agent
   ---
   ```

3. In the command body, invoke the target agent by its registered name using the
   `Agent` tool:
   ```
   result = invoke Agent({
     agent: "dark-factory-agent",
     prompt: "<pass through user input verbatim>"
   })
   return result
   ```

4. Do NOT reference the agent's `.md` file path inline (e.g., `Follow the
   instructions in agents/dark-factory/agents/dark-factory-agent.md exactly.`).
   This style worked when the command was called from the plugin root as CWD, but
   fails in nested sessions where CWD is different — Claude Code cannot resolve the
   relative path and falls back to running orchestration logic inline, bypassing
   the intended agent flow entirely.

5. The command body should contain no orchestration logic itself. Its sole
   responsibility is to pass inputs through to the named agent.

## Notes

- The failure mode for path-based references is silent: in a nested session the
  agent is not invoked, but the command doesn't error. Instead, the current Claude
  instance attempts to execute the instructions from memory or improvise, producing
  unpredictable results.
- Invoking by name (`agent: "dark-factory-agent"`) is CWD-independent — Claude
  Code resolves the agent by its registered slug, not by filesystem path.
- If the agent needs access to specific tools (e.g., `Bash`, `Read`), those must
  be declared in the agent's own frontmatter `tools:` field, not in the command
  file's frontmatter. The command file only needs `tools: Agent`.
- This pattern is enforced by `tests/test_agent_flow_deviation_nested.py`, which
  asserts that `commands/manufacture.md` uses `invoke Agent({ agent: "dark-factory-agent" ... })`.
