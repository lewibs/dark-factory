---
name: investigation-delegate
description: "Use this skill when an agent needs to understand how a system or component works before proceeding — delegate that research to investigation-agent rather than doing it inline."
user-invocable: false
---
## When to use

Any time an agent would otherwise start reading source files, grepping the repo, or exploring tests to understand an unfamiliar system. Instead, delegate to `investigation-agent` and use its returned documentation.

Concrete triggers:
- Before making code changes to a system the agent does not fully understand
- Before writing tests for a system
- When planning changes that may affect other parts of the codebase
- When the agent needs to understand component interactions or system architecture

## Steps

1. Identify the system or component name (e.g. `"repair-agent"`, `"metrics"`, `"dark-factory-hooks"`).
2. Invoke `investigation-agent` with the system name and an optional specific question:

   ```
   result = invoke investigation-agent({
     system: "<system-name>",
     question: "<specific question, or blank for general overview>"
   })
   ```

3. Check the result:
   - If `result.error`: log `"doc lookup failed for <system>, continuing with partial knowledge"` and proceed with best effort.
   - If success: use `result.content` (the documentation) to inform your work. The file is also written to `docs/docs/<system-name>.md` for future agents.

4. Do not repeat the research yourself. Trust the returned documentation as authoritative.

## Notes

- Investigation-agent checks `docs/docs/<system-name>.md` first and returns it immediately if it exists — no staleness check. Existing docs are treated as authoritative.
- If the doc does not exist, investigation-agent explores the source code and tests to create it, then returns the new content.
- Never inline research (grep, file reads, bash exploration) when investigation-agent can provide this. Delegating keeps knowledge centralized and speeds up future agents who hit the same system.
- Errors from investigation-agent should never block an agent's primary task — log and continue.
- **Never invoke the built-in `Explore` subagent_type directly.** `Explore` bypasses the docs cache and always scans the codebase from scratch. Any agent that has access to the `Agent` tool must route codebase research through `investigation-agent` instead. This rule applies to all 12 Agent-capable agents in this codebase and should be enforced by adding an explicit note to each agent's `.md` file in the format: `Never invoke the built-in \`Explore\` subagent_type directly. Always route codebase research through \`investigation-agent\` — it checks existing docs first (cheap) before scanning the codebase.`
