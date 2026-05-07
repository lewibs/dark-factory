---
name: agent-diagnosis-action-boundary
description: "Use this skill when writing multi-agent debug or fix flows to ensure agents implement fixes (not just diagnose), commit responsibility is assigned to exactly one agent, and retry loops have explicit iteration caps."
user-invocable: false
---
## When to use

Any time you write or update a multi-agent flow that involves debugging, diagnosing, or fixing code — for example: debugger-agent, debug-flow-agent, ralph-fix-and-push, or any orchestrator that calls a sub-agent to identify and resolve a bug.

## Steps

1. **Forbid stopping at diagnosis.** Every agent in a fix flow must be explicitly told it must implement the fix, not just diagnose. Add a sentence like:
   ```
   You do not stop at diagnosis — you diagnose AND fix.
   ```
   Or in an orchestrator:
   ```
   It is NOT acceptable to stop at diagnosis.
   ```

2. **Assign commit responsibility to exactly one agent.** In a chain of agents (e.g., debugger-agent → debug-flow-agent → orchestrator), only ONE agent should commit. The others must leave changes in the working tree. Document this explicitly in each agent:
   - The agent that implements the fix: "Do NOT commit — leave all changes in the working tree. Committing is the responsibility of <agent-name>."
   - The agent that commits: "After <sub-agent> completes, commit all changes: `git add --all && git commit -m "..."`"

3. **Verify before commit.** The committing agent must verify that the fix was actually applied before committing:
   ```
   Run `git diff --exit-code` to confirm code changes exist in the working tree. If no changes, the fix was not applied.
   Run the full test suite to confirm the fix works before committing.
   ```

4. **Cap retry loops at a small explicit number.** Any loop that invokes a sub-agent for re-attempts must have a named iteration cap (e.g., 3 total iterations). Document it as:
   ```
   If after 3 total iterations the fix is still not working, return exit_code=1 with the bug explanation and last test failure output.
   ```

5. **Propagate failure clearly.** If a sub-agent returns without implementing a fix (no working tree changes, no passing tests), the parent agent must report failure with diagnostic output — not silently succeed or skip the PR step.

6. **Update allowed-tools.** Any agent that commits must include `Bash(git *)` in its `allowed-tools` front-matter. Any agent that only applies changes to the working tree does NOT need git commit tools.

## Notes

- The most common failure mode is an agent that returns a diagnosis document but no code changes — the parent silently accepts this and opens an empty or missing PR.
- The second most common failure mode is two agents both trying to commit: the first commits an empty diff, the second has nothing left to commit. Assign commit to exactly one.
- Verification before commit (`git diff --exit-code` + test run) catches both failure modes at the boundary where they are cheapest to detect.
- This pattern was introduced fixing debugger-agent, debug-flow-agent, and fix-flow-orchestrator in the 2026-05-07 debug-flow-mandate-action task.
