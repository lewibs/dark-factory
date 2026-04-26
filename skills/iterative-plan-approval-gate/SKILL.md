---
name: iterative-plan-approval-gate
description: "Implements a human approval gate for a plan file: opens it in VS Code, displays it inline, sends a PushNotification, then loops on developer feedback until explicit approval or abort."
user-invocable: false
---
## When to use

Use this pattern whenever an orchestration agent must block on developer approval of a written artifact (plan file, config, spec) before proceeding to an irreversible action such as code generation or deployment.

## Steps

1. After receiving a `planPath` from the upstream agent (e.g. `planning-agent`):

   a. Invoke the `open-in-vscode` skill with `planPath` so the file opens in the developer's editor immediately (non-fatal if the `code` CLI is absent).

   b. Read the file at `planPath` using the `Read` tool.

   c. Display inline: `"Plan written to <planPath>. Please review."` followed by the full file contents.

   d. Call `PushNotification` with:
      - title: `"Plan Approval Required"`
      - message: `"A plan is ready for your review and requires approval to proceed."`

   e. Ask the developer:
      ```
      "Approve this plan? Reply 'yes' or 'approve' to proceed to implementation,
       'abort' to cancel, or provide feedback text to request a revision."
      ```

2. Normalize the developer's reply: `response = lowercase(developer's reply)`.

3. Branch on `response`:
   - `"abort"` — report `"Feature work aborted by developer."` and STOP.
   - `"yes"` or `"approve"` — break out of the loop and proceed to the next stage.
   - Anything else — treat as revision feedback: re-invoke the upstream planning agent with the feedback text, receive the new `planPath`, then return to step 1.

## Notes

- **Lowercase normalization is required.** Without it, replies like "Yes", "YES", or "Approve" will fall through to the feedback branch and trigger an unintended plan revision loop.
- **Both tools must be declared in `tools:` front-matter.** Any agent implementing this pattern needs `PushNotification` and `Skill` in its `tools:` list. Omitting either causes the tool to be silently unavailable at runtime. See the `declare-tools-in-agent-frontmatter` skill.
- **Double-open is intentional.** The upstream planning agent already calls `open-in-vscode` when it writes the plan. The orchestrating agent calls it again here as a belt-and-suspenders guarantee — if the planning agent's call was skipped or failed, the file still opens for the developer.
- **Keep the original description across retries.** When passing feedback to the planning agent, always include the original feature description alongside the feedback so the planner has full context: `"Revise the plan based on this feedback: <feedback>\n\nOriginal description: <description>"`.
- The `abort` path is an expected (non-error) exit — report it cleanly to the developer and stop; do not propagate as an exception.
