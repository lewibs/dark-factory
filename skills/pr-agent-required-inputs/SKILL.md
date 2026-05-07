---
name: pr-agent-required-inputs
description: "Use this skill when invoking pr-agent to ensure the required context inputs (taskDescription or planFilePath) are always provided so pr-agent can write a meaningful PR description."
user-invocable: false
---
## When to use

Any time you write or update an agent that invokes `pr-agent` as a sub-agent. pr-agent requires at least one context input to write a proper PR title and description — if neither is provided, it will produce a generic or empty PR description.

## Steps

1. **Always pass either `taskDescription` or `planFilePath`** when invoking pr-agent:
   - `taskDescription` — a string describing what was fixed or implemented (e.g., the contents or path of a bug audit log)
   - `planFilePath` — path to a plan file (e.g., `docs/plans/<plan>.md`) that documents the work done

2. **For debug/fix flows**, pass the bug audit log as context:
   ```
   invoke pr-agent with:
     taskDescription = <contents or summary from bug audit log written by debugger-agent>
     bugFilePath = docs/bugs/<yyyy-mm-dd>-<bug-slug>.md
   ```

3. **For feature flows**, pass the plan file:
   ```
   invoke pr-agent with:
     planFilePath = docs/plans/<plan-name>.md
   ```

4. **Do not invoke pr-agent with no context.** An invocation like `invoke pr-agent({})` or `spawn pr-agent with no arguments` will produce a low-quality PR description and may cause pr-agent to fail.

5. **Verify pr-agent returns a valid PR URL.** After invocation, check that the returned value contains a non-empty `pr_url`. If it does not, treat this as a failure — do not silently continue.

## Notes

- `pr-agent` does not merge. It opens the PR, waits for CI to pass, and resolves review threads. The caller is responsible for deciding when to merge. See also: `pr-agent-does-not-merge` skill.
- `bugFilePath` is a convenience input for debug flows — it lets pr-agent link to the bug audit log directly in the PR description.
- The `taskDescription` field accepts free-form text, so passing the full text of a bug audit log is valid and encouraged for debug fix PRs.
- This pattern was introduced fixing debug-flow-agent in the 2026-05-07 debug-flow-mandate-action task, where pr-agent was being invoked without required context inputs.
