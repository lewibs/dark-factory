# dark_factory

A fully autonomous coding plugin for Claude Code that builds features, fixes bugs, and repairs broken integration flows end-to-end — from planning through code review, PR, and merge — with no manual intervention.

This project is documented in `docs/`. See:

- `docs/docs/` — authoritative system documentation (source of truth for how this codebase works)
- `docs/plans/` — implementation plans for completed and in-progress work
- `docs/bugs/` — debugged and solved issues (audit logs)

## Investigation Agent Pattern

When you need to understand how a system or component works before proceeding with your task, delegate the investigation work to `investigation-agent`:

### When to use investigation-agent

Invoke investigation-agent whenever you need authoritative documentation about a system to proceed with your work:
- Before making code changes to a system you don't fully understand
- When you need to understand component interactions or system architecture
- Before writing tests for a system
- When planning changes that may affect other parts of the codebase

### How to invoke investigation-agent

Invoke investigation-agent with a system name and optional question:

```
result = invoke investigation-agent({
  system: "<system-name>",
  question: "<specific question or blank for general overview>"
})

if result.error:
  log("doc lookup failed for " + system + ", continuing with partial knowledge")
  continue with best effort
else:
  documented_system = result.content
  # Use documented_system to inform your work
```

Investigation-agent will:
1. Check if documentation exists in `docs/docs/<system-name>.md`
2. If docs exist, return them immediately (no staleness check — they are treated as authoritative)
3. If docs do not exist, investigate the source code and tests, then create new documentation
4. Return the documentation content and metadata to you for use in proceeding with your work

### Error handling

If investigation-agent returns an error (system not found, investigation failed):
- Log the error but do not block your work
- Continue with the knowledge you have
- Optionally note the gap in the PR or task for future investigation

### Example

Before refactoring the repair-agent flow, you invoke investigation-agent:

```
result = invoke investigation-agent({
  system: "repair-agent",
  question: "What is the repair-agent flow and how does it integrate with dark-factory?"
})

# result.content now contains authoritative docs about repair-agent
# Use this to inform your refactoring decisions
```
