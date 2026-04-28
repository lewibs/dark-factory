---
name: iterative-plan-approval-gate
description: "Implements human approval gates for a plan file: either a single gate for the full document, or a cascading section-by-section gate (draft → diagram → per-flow → final) driven by a depth-2 orchestrator."
user-invocable: false
---
## When to use

Use this pattern whenever an orchestration agent must block on developer approval of a written artifact (plan file, config, spec) before proceeding to an irreversible action such as code generation or deployment.

There are two variants:

- **Single-gate** — present the full artifact once and loop on feedback until approval or abort. Use when the artifact is small or has only one logical section.
- **Section-by-section cascade** — present each section of the artifact separately, looping on feedback per section, then do a final full-plan confirmation before execution. Use when the artifact has multiple independently reviewable sections (e.g., System Intent, Mermaid diagram, per-flow pseudocode). This variant was introduced to surface planning approval gates to the human when a sub-planning-agent operates at depth-3 and cannot call AskUserQuestion directly.

## Single-gate Steps

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

## Section-by-section Cascade Steps

This variant is used when a worker sub-agent (depth-3) builds the plan incrementally, one section per invocation, and the orchestrator (depth-2) owns all AskUserQuestion calls.

1. **Phase: Draft / System Intent**

   a. Invoke the planning sub-agent with `phase="draft_plan"` and the original task description as feedback.

   b. Receive `planPath` from the sub-agent.

   c. Read `planPath` and extract the `## System Intent` section.

   d. Call `PushNotification` with title `"Draft Plan Ready"`.

   e. Use `AskUserQuestion` with options `["Looks good — continue to Mermaid diagram", "Request Changes"]`.

   f. If `"Request Changes"`: use the developer's typed feedback as the new feedback value and repeat step a. Otherwise break.

2. **Phase: Mermaid Diagram**

   a. Invoke the planning sub-agent with `phase="mermaid"`, the existing `planPath`, and `feedback="none"` (or developer feedback on retry).

   b. Receive `{ planPath, url }`. If `url` is non-null, push a notification with the diagram URL.

   c. Read `planPath` and extract the `## Mermaid Diagram` section. If `url` is null, note in the question text that rendering failed.

   d. Use `AskUserQuestion` with options `["Approve — continue to flows", "Request Changes"]`.

   e. If `"Request Changes"`: capture feedback and repeat step a. Otherwise break.

3. **Phase: Flows (one at a time)**

   a. Read `planPath` and scan for `### Flow:` headings to get an ordered list of flow names.

   b. For each `flowName`:

      i. First pass: read and display the existing `### Flow: <flowName>` section directly from `planPath` (no sub-agent call needed unless feedback was given).

      ii. Use `AskUserQuestion` with options `["Approve — continue to next flow", "Request Changes"]`.

      iii. If `"Request Changes"`: invoke the planning sub-agent with `phase="flows"`, `planPath`, `feedback=<developer text>`, `flowName=<flowName>`. Re-read the updated section and repeat step ii.

      iv. On approval: advance to the next flow.

4. **Final full-plan confirmation**

   a. Invoke `open-in-vscode` skill with `planPath`.

   b. Read and display the full plan file.

   c. Call `PushNotification` with title `"Plan Approval Required"` and message `"All sections approved. Final plan review required before implementation begins."`.

   d. Use `AskUserQuestion` with options `["Approve — start implementation", "Abort"]`.

   e. If `"Abort"`: report and STOP. Otherwise proceed to execution.

## Notes

- **Lowercase normalization is required.** Without it, replies like "Yes", "YES", or "Approve" will fall through to the feedback branch and trigger an unintended plan revision loop.
- **Both tools must be declared in `tools:` front-matter.** Any agent implementing this pattern needs `PushNotification` and `Skill` in its `tools:` list. Omitting either causes the tool to be silently unavailable at runtime. See the `declare-tools-in-agent-frontmatter` skill.
- **Double-open is intentional.** The upstream planning agent already calls `open-in-vscode` when it writes the plan. The orchestrating agent calls it again here as a belt-and-suspenders guarantee — if the planning agent's call was skipped or failed, the file still opens for the developer.
- **Keep the original description across retries.** When passing feedback to the planning agent, always include the original feature description alongside the feedback so the planner has full context: `"Revise the plan based on this feedback: <feedback>\n\nOriginal description: <description>"`.
- The `abort` path is an expected (non-error) exit — report it cleanly to the developer and stop; do not propagate as an exception.
- **Section-by-section variant: do not re-invoke the sub-agent for the first pass of each flow.** The sub-agent already wrote the flow section when it built the plan. Only call the sub-agent again when the developer has provided feedback for that specific flow. This avoids redundant work and prevents unintended section rewrites.
- **Section-by-section variant: all AskUserQuestion calls must live in the depth-2 orchestrator.** The depth-3 planning sub-agent must be a pure phase-delegator with no user interaction. See the `askuserquestion-depth-limit` skill for why depth-3 AskUserQuestion calls are silently auto-answered and never reach the human.
