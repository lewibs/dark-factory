---
name: claude-md-for-cross-cutting-guidance
description: "Use this skill when a new pattern or convention needs to apply to all agents — write it once in CLAUDE.md rather than editing every agent file individually."
user-invocable: false
---
## When to use

When a task introduces a new convention, pattern, or protocol that should apply to every agent in the system. Examples:
- A new shared agent to delegate work to (e.g. investigation-agent, metrics-agent)
- A new output format or structured return protocol all agents must follow
- A new error handling convention (e.g. return-question protocol)
- A new tool or skill all agents should be aware of

Do NOT use this approach for agent-specific logic — only for genuinely cross-cutting concerns.

## Steps

1. Confirm the pattern is truly cross-cutting (affects all or most agents, not just one or two).
2. Draft the guidance as a named section in `CLAUDE.md`:
   - Give the section a clear heading (e.g. `## Investigation Agent Pattern`)
   - Include: when to use it, how to invoke it (with pseudocode), and error handling
   - Include a concrete example showing a realistic invocation
3. Write or update the `CLAUDE.md` section. Do not edit individual agent files unless the agent has special-case behavior that differs from the global pattern.
4. Verify the section is self-contained — an agent reading only `CLAUDE.md` should understand the pattern without needing to read additional files.
5. Optionally, create a companion skill file in `skills/` that documents the same pattern in more detail, so agents can be pointed to it by path for deeper reference.

## Notes

- CLAUDE.md is injected into every agent's context automatically. A single update propagates to all agents immediately, with no per-agent file editing required.
- This approach avoids bulk edits that can introduce drift or inconsistency across agent files.
- When the cross-cutting pattern becomes complex, the companion skill file (referenced from CLAUDE.md by path) is the right place for detailed steps. Keep the CLAUDE.md entry concise and focused on the decision: when and how.
- If only 1-2 agents need a behavior, edit those agents directly instead of polluting the global context.
