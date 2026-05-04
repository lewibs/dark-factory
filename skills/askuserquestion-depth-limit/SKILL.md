---
name: askuserquestion-depth-limit
description: "AskUserQuestion and PushNotification only reach the human when called from a depth-2 agent (direct child of the CLI); calls from depth-3+ sub-agents are auto-answered by the parent agent and never surface to the user."
user-invocable: false
---
## When to use

Apply this rule whenever you design or refactor an agent hierarchy that needs human approval, confirmation, or input at any point in the flow. If a future refactor moves user-interaction logic into a deeper sub-agent, this skill explains why the interaction will silently break.

## Steps

1. **Identify the depth of each agent in the call chain.**
   - Depth 1: the Claude Code CLI itself (the human's terminal).
   - Depth 2: the first `Agent` tool call spawned by the CLI command (e.g. `dark-factory-agent`, `feature-agent` when invoked directly).
   - Depth 3: sub-agents spawned by a depth-2 agent (e.g. `planning-agent` spawned by `feature-agent`).
   - Depth 4+: sub-agents spawned by depth-3 agents, and so on.

2. **Place all `AskUserQuestion` and `PushNotification` calls at depth 2 only.**
   - A depth-2 agent's `AskUserQuestion` surfaces to the actual human user in the CLI.
   - A depth-3+ agent's `AskUserQuestion` is intercepted and auto-answered by its parent agent — the human never sees it.

3. **Make deeper agents pure workers: no user interaction.**
   - Agents at depth 3 and below must not list `AskUserQuestion` or `PushNotification` in their `tools:` frontmatter.
   - These agents receive all needed context from their parent as structured input and return structured output — they never pause for human input.

4. **When refactoring a monolith agent into an orchestrator + worker split:**
   - Confirm which agent will sit at depth 2 after the split.
   - All `AskUserQuestion` loops must stay in that depth-2 agent.
   - The worker (depth 3) must be a pure phase-delegator: receive input, do work, return output.
   - See the `haiku-orchestrator-worker-split` skill for the full split pattern.

5. **Audit after any restructuring.**
   - After any agent hierarchy change, grep for `AskUserQuestion` across all agent `.md` files.
   - For each occurrence, verify the agent is at depth 2 in the call chain, not deeper.
   ```bash
   grep -r "AskUserQuestion" agents/ --include="*.md" -l
   ```

## Notes

- **The symptom is silent auto-approval.** When this bug occurs, the parent agent sees the `AskUserQuestion` call from its child, answers it with an affirmative (or the first option), and execution continues — the developer never gets a chance to review or reject. There is no error, no log, and no indication that the gate was bypassed.
- **The fix is always structural, not parametric.** You cannot pass a flag or set an option to make a depth-3 `AskUserQuestion` reach the human. The only fix is to move the interaction up to depth 2.
- **The canonical example:** `planning-agent` was originally a monolith at depth 2 that used `AskUserQuestion` for plan approval. After the `haiku-orchestrator-worker-split` refactor, `feature-agent` became depth 2 and `planning-agent` became depth 3. All `AskUserQuestion` calls had to move from `planning-agent` into `feature-agent`. Any `AskUserQuestion` left in `planning-agent` would be silently auto-answered by `feature-agent`.
- **`PushNotification` has the same constraint.** Although notifications failing silently are less catastrophic than approval gates failing silently, keep `PushNotification` at depth 2 for the same structural reason.

## Anti-pattern: multi-turn relay loop (status:question protocol)

A common workaround when the correct depth-2 agent cannot use `AskUserQuestion` is to implement a relay protocol where:
- The depth-2 agent returns `{ status: "question", question: "...", options: [...] }` instead of calling `AskUserQuestion` itself.
- The depth-1 orchestrator catches `status == "question"`, calls `AskUserQuestion`, then re-invokes the depth-2 agent with `{ answer: <user answer> }`.

This pattern is fragile and should not be used. The problems:
- Every interaction round-trip re-invokes the depth-2 agent from scratch, paying full context-reconstruction cost.
- State must be passed through plan files or external storage between invocations, creating new failure modes.
- The orchestrator grows complex loop logic that belongs in the agent.
- Any agent that previously called AskUserQuestion directly only needs to check its own depth — if it is at depth 2, it can and should call `AskUserQuestion` directly.

**The correct design:** if the agent that owns the interaction logic is at depth 2 (direct child of the CLI command), declare `AskUserQuestion` in its `tools:` frontmatter and call it directly. Remove the relay loop from the parent. The `feature-agent` fix in the manufacture flow (2026-05-04) is the canonical example: the multi-turn relay was removed from `dark-factory-agent` and `AskUserQuestion` was restored in `feature-agent`, which is already at depth 2.
