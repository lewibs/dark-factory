---
name: subagent-must-not-own-shared-resource-cleanup
description: "Sub-agents invoked by an orchestrator must never own cleanup of shared resources (worktrees, brain.json, temp dirs) the orchestrator still needs after the sub-agent returns — SubagentStop fires before the orchestrator regains control."
user-invocable: false
---
## When to use

Whenever you are wiring a `SubagentStop` hook to a sub-agent that is called from inside an orchestrating agent (e.g. `dark-factory-agent` calling `pr-agent`). Ask: "Does this cleanup script destroy something the orchestrator will touch in its next step?" If yes, do not wire the cleanup to the sub-agent's stop hook.

Also apply this when reviewing existing sub-agent hook scripts that delete worktrees, remove `brain.json`, or clean up shared temp files.

## Steps

1. Identify which agent is the **orchestrator** (owns the full workflow lifecycle) and which agents are **sub-agents** (invoked by the orchestrator to complete a single phase).

2. List all shared resources the orchestrator reads or writes after each sub-agent returns:
   - Feature worktrees (`$WORK_DIR`)
   - `brain.json` / `brain-patch.json`
   - Shared temp directories
   - Any file the orchestrator reads in a step that follows the sub-agent call

3. For each sub-agent's `SubagentStop` hook script, verify it does NOT delete or mutate any resource from Step 2.
   - Safe: commit files, write a patch, log metrics, send a notification
   - Unsafe: `rm -rf "$WORK_DIR"`, `rm -f brain.json`, `git worktree remove`

4. If an unsafe cleanup exists on a sub-agent, move the cleanup to the **orchestrator's** own cleanup path (its `Stop` hook, or an explicit step at the end of its instruction flow after all sub-agents have returned).

5. Add the cleanup responsibility to the orchestrator's documented step list (e.g., "Step 11: cleanup worktree") so future maintainers know it is intentionally there and not accidentally missing from sub-agents.

## Notes

- **Root cause of the double-cleanup bug**: `pr-agent` had a `SubagentStop` hook that called `cleanup-worktree.sh`. When `dark-factory-agent` invoked `pr-agent` as a sub-agent, the hook fired the moment `pr-agent` finished — before `dark-factory-agent` resumed execution. The worktree was deleted, and `dark-factory-agent` Steps 11-12 (skill-update-agent invocation and final cleanup) failed silently or got stuck. The symptom was a manufacture run that appeared to never complete.
- `SubagentStop` fires synchronously when the sub-agent's session ends, not when the orchestrator's `await` returns. There is no safe window in which a sub-agent can perform cleanup of shared state "after the orchestrator is done."
- The orchestrator owns the lifecycle of every resource it creates. Sub-agents are guests in that lifecycle. A sub-agent should clean up only resources it created itself and that the orchestrator does not reference.
- This is distinct from the `subagent-stop-in-agent-frontmatter` skill (which documents where to declare `SubagentStop`) — this skill addresses what the hook script is allowed to do.
- If a sub-agent genuinely needs to clean up a resource on abnormal exit (e.g., to avoid leaked temp files when the orchestrator itself crashes), use a flag file: the sub-agent writes a "I finished normally" marker; the orchestrator's own `Stop` hook checks the flag and decides whether to clean up.
