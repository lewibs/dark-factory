# manufacture-command

## Metadata

- System type: `command`

## System Intent

- What this is: `commands/manufacture.md` is the Claude Code slash command entry point for `/dark-factory:manufacture`. It is a thin dispatcher — its sole responsibility is to invoke `dark-factory-agent` as a sub-agent via the Agent tool and return its result unchanged. It contains no orchestration logic.

## Dispatch Mechanism

`commands/manufacture.md` invokes `dark-factory-agent` via the Agent tool:

```
result = invoke Agent({
  agent: "dark-factory-agent",
  prompt: "taskDescription: <taskDescription>\ntaskName: <taskName if provided>"
})

return result
```

`commands/manufacture.md` declares `tools: Agent` in its frontmatter, which grants it the ability to spawn sub-agents. All orchestration logic (task classification, worktree prep, routing to worker agents, code review, documentation, PR, cleanup) is owned by `dark-factory-agent`. The manufacture command never inspects, modifies, or filters the result — it passes it through to the caller as-is.

### Why sub-agent invocation

Previous versions of `commands/manufacture.md` contained inline instructions (e.g., a relative path to `dark-factory-agent.md` or a direct `Follow the instructions in ...` directive). This caused Claude to attempt orchestration inline rather than delegating to the dedicated agent, leading to flow deviation. The Agent tool invocation enforces hard isolation: `dark-factory-agent` runs in its own sub-agent context with its own instruction set, preventing the manufacture command layer from interfering.

## Flows

### Flow: `manufacture-command.dispatch`

- Core files: `commands/manufacture.md`, `agents/dark-factory/agents/dark-factory-agent.md`

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `manufacture-command.dispatch.success` | `taskDescription`, optional `taskName` | `dark-factory-agent` result (PR URL) | happy path | sub-agent runs to completion and returns |
| `manufacture-command.dispatch.error` | `taskDescription` | error from sub-agent | error | `dark-factory-agent` returns an error or hard-stop; manufacture-command passes it through |

#### Pseudocode

```
invoke Agent(agent="dark-factory-agent", prompt=<taskDescription + taskName>)
return result as-is
```

## Logs

| Source | Location |
|--------|----------|
| agent execution | Claude Code session transcript |
| brain state | `$WORK_DIR/brain.json` (managed by dark-factory-agent) |

## Deployment

- Mechanism: `Claude Code slash command`
- Invocation: `/dark-factory:manufacture`
- Notes: Requires dark-factory plugin installed. The `tools: Agent` frontmatter directive must be present for Claude Code to allow sub-agent invocation from this command.
