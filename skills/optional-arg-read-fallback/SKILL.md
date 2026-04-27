---
name: optional-arg-read-fallback
description: "When adding an optional shared-state argument (e.g. brainPath) to a sub-agent, always guard every read/write with an existence check and fall back to caller-supplied args — never break backward compatibility."
user-invocable: false
---
## When to use

When modifying an existing sub-agent to accept a new optional argument that provides richer context (e.g. a shared state file path), but the agent must remain callable by older orchestrators or test harnesses that do not provide the new argument.

The canonical example in this codebase is `brainPath` — an optional path to `brain.json` that all dark-factory sub-agents accept. Feature-agent, debugger-agent, repair-agent, code-review-orchestrator-agent, update-documentation-agent, skill-update-agent, and pr-agent all follow this pattern.

## Steps

1. Add the optional argument to the agent's function signature with a clear comment that it is optional:
   ```
   myAgent(requiredArg, optionalArg):   # optionalArg may be null/absent
   ```

2. At every point where you would read from or write to the optional resource, guard with:
   ```
   if optionalArg is provided and file/resource exists:
     # perform the read or write
   else:
     # use requiredArg / caller-supplied arguments as-is (no change to current behavior)
   ```

3. When the optional arg provides a value that supersedes a caller-supplied arg (e.g. `brain.planFilePath` is richer than a bare `planFilePath` passed directly), prefer the optional-arg value only when it is non-null:
   ```
   if brain.planFilePath is not null:
     planFilePath = brain.planFilePath
   ```

4. Document the fallback behavior explicitly in the agent's Notes section:
   ```
   - `<optionalArg>` is optional — if not provided or file not readable, fall back to current behavior (no reads/writes).
   ```

5. Never make the optional arg mandatory in downstream calls. Pass it forward as-is (including null) so that if the outer caller did not provide it, the inner chain also runs without it.

## Notes

- The pattern preserves backward compatibility: tests, manual invocations, and older orchestrator versions that do not pass the new arg continue to work unchanged.
- "File exists" check is important — do not assume the file was successfully written by a previous step. A race or failure upstream may leave it absent.
- This pattern is distinct from a required handoff field: a required field must always be present and should cause a hard-stop if missing. Use the readFallback pattern only for enrichment args that improve context but are not essential for correctness.
