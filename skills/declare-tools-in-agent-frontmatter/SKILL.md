---
name: declare-tools-in-agent-frontmatter
description: "Ensures every tool called in an agent's instruction body is listed in the tools: YAML front-matter, and every skill invoked in the body is listed in the skills: front-matter. Both fields act as access-control gates — omitting either causes the tool or skill to be silently unavailable at runtime."
user-invocable: false
---
## When to use

Use this whenever you create or modify an agent file (any `agents/**/*.md`) that calls a tool or invokes a skill in its instruction body. Also use it when debugging an agent that appears to skip a step silently (no error, but no effect).

## Steps

1. Open the agent file and read its YAML front-matter block (the section between the opening and closing `---` delimiters).
2. **Tools check:**
   a. Identify the `tools:` field. If it is absent, add it.
   b. Read the agent instruction body and collect every tool the agent is instructed to call (look for tool names like `PushNotification`, `Read`, `Bash`, `Agent`, `WebSearch`, `Task`, etc.).
   c. For each tool found in the body, confirm it is listed in the `tools:` front-matter field. If it is missing, add it to the comma-separated list.
3. **Skills check:**
   a. Identify the `skills:` field. If the agent body references any skill (e.g., `invoke skills/logging/SKILL.md`, `use skills/deviation-protocol/SKILL.md`), the field must be present.
   b. Read the agent instruction body and collect every skill slug referenced (the directory name under `skills/`, e.g., `logging`, `deviation-protocol`).
   c. For each skill slug found in the body, confirm it appears in the `skills:` front-matter field (comma-separated). If it is missing, add it.
4. Save the file.
5. Repeat for every agent file that was created or touched in the current task.

## Notes

- Claude Code grants an agent access to a tool **only** if that tool appears in the agent's `tools:` front-matter field. A tool referenced in the instruction body but absent from `tools:` is silently inaccessible — the agent will not error, it will simply skip or never reach that call.
- The same gate applies to skills: if a skill slug is invoked in the body but omitted from `skills:`, the agent cannot load it at runtime.
- `PushNotification` is particularly easy to miss because it was added to agent bodies as a "notify before blocking on input" pattern after the initial `tools:` lists were written. Any future agent that adds this pattern must remember to add `PushNotification` to `tools:` as well.
- `Skill` must be listed in `tools:` whenever an agent invokes any skill via the `Skill` tool. If an existing agent file gains its first skill invocation, `Skill` must be added to `tools:` at the same time — it is not implicitly available. This was a concrete omission discovered when adding the `open-in-vscode` skill call to `feature-agent`.
- The `allowed-tools:` field (which restricts which sub-commands of `Bash` are permitted) is separate from `tools:` — both may need to be updated when adding new tool usage. For example, when an agent is updated to perform local git operations, add the required git subcommands explicitly:
  ```yaml
  allowed-tools: Bash(bash *), Bash(find *), Bash(git add *), Bash(git commit *), Bash(git checkout *), Bash(git branch *)
  ```
  Without these entries, the agent will be blocked from running those git commands at runtime.
- A regression test (`tests/test_push_notification_declared.py`) exists in this repo that parses the YAML front-matter of all agent files and asserts `PushNotification` is present in `tools:` for every agent that references it in its body. Run this test after modifying agent files to catch omissions early.
- When adding a new skill invocation to an existing agent (e.g., adding `skills/logging/SKILL.md` to `implementation-agent.md`), always update the `skills:` field in the same edit — do not treat it as optional cleanup.
- **The `skills:` field lists skill directory slugs only — never agent names.** A common mistake when auditing is to add agent names (e.g., `debugger-fix-agent`, `reproduce-test-agent`) to the `skills:` field because they appear as invocation targets in the instruction body. The `skills:` field must only contain directory slugs that exist under `skills/` (e.g., `investigation-delegate`, `logging`). Sub-agents invoked via the `Agent` tool do not belong in `skills:` at all — they are resolved by name at runtime, not through the skill loader. Putting agent names in `skills:` results in a load error or silent no-op.
- **Doer agents should have broad CLI access by default.** Agents that execute work (implementation-agent, testing-agent, debugger-agent, debug-flow-agent, ralph-fix-and-push, repair-agent) must include `aws`, `gh`, `git`, and `docker` in their `allowed-tools`. Restricting `allowed-tools` to only specific test runners (e.g., `pytest`, `npm test`) assumes a pure local project and silently degrades on cloud-native or infrastructure projects — the agent will not error; it will simply do the best it can with read-only tools and return a plausible-looking but incomplete or incorrect result. The canonical baseline for doer agents is:
  ```yaml
  allowed-tools: Bash(pytest *), Bash(python *), Bash(npm test *), Bash(bash *), Bash(mkdir -p *), Bash(find *), Bash(grep -r *), Bash(aws *), Bash(gh *), Bash(git *), Bash(docker *), Bash(curl *)
  ```
  Orchestrator agents (those that only plan and delegate) do not need this expansion.
