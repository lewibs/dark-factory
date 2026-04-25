---
name: new-plan
description: Create a new plan in docs/plans using a gated workflow: Mermaid diagram, black-box I/O contracts, acceptance-test criteria, optional pseudocode, then tests-first file checklist. Use when starting a new plan before implementation.
---

## Required

Use this skill whenever a new plan must be authored in `docs/plans/`.

Follow `.agent/workflows/development-flow.md` for the canonical end-to-end sequence and gates.

1. Start from `templates/plan-template.md`. Do not invent alternate section order.
2. Choose plan type: `plan` or `sub-plan`.
3. Set plan `Status` to `draft` while authoring.
4. Complete the plan in strict stage order. Do not move to the next stage until the user explicitly approves the current one.
5. Stage 1: Mermaid diagram (approval required).
   - Follow `.agent/skills/create-mermaid-diagram/SKILL.md`.
   - Use user input about what they are building to define nodes, boundaries, and labeled data flows.
   - When a boundary points to another planned subsystem, reference the owning plan file in `docs/plans/*.md` (plan-to-plan boundary), not an internal implementation file from that other subsystem.
6. Stage 2: Black-box input/output contracts of the system, not of the internal parts of the system (approval required).
   - Define input and output types, fields, validation rules, and transformation behavior.
   - Capture success and failure outputs.
   - Keep this at contract level (example class of inputs: auth primitives such as `email`, `code`, `magic_link_token`).
   - If contracts are owned by another plan, reference that plan file as the source-of-truth contract owner.
   - Every `### Flow` heading must include test mapping:
     - Use one or more concrete test file paths when automated tests are required.
     - Use explicit `N/A` only when no automated test is required for that flow.
   - Every contract table must include an `updated` column; set `Y` for rows changed in the current revision.
7. Stage 3: Acceptance criteria and plan-first tests (approval required).
   - Require user-provided test flows.
   - For each flow, capture inputs and pass/fail rules (expected outputs should be embedded in the pass criteria).
   - Check whether important flows are missing and recommend additional tests (happy path, error path, and edge cases) before moving forward.
   - Design tests from the plan contract, not from code behavior.
8. Stage 4: Pseudocode for critical flows/functions (optional, approval required if included).
   - Keep this concise and focused on implementation strategy.
   - If the user does not want pseudocode, mark the section as skipped with a reason.
9. After all stages are approved, set final status by meaning:
   - `approved`: approved but not yet applied in code.
   - `documentation`: code currently exists and matches the plan contract.
10. After all stages are approved, transition to `.agent/skills/reconcile-plans/SKILL.md` to propagate contract impacts and link updates across related plans.
11. Before any implementation begins, require a planning PR and human review gate:
   - Create a PR for the plan/reconciliation diff using `.agent/skills/create-pull-request/SKILL.md`.
   - Wait for explicit human approval (or merge) before invoking `.agent/skills/execute-plan/SKILL.md`.

## Context

Treat plans as source-of-truth contracts, not implementation notes.

- Stage gates are mandatory and sequential.
- Black-box first: interfaces and behavior before internals.
- Test intent comes from acceptance criteria captured in the plan.
- Plan approval happens before implementation starts.
- Human plan-review PR gate is mandatory before implementation starts.
- Status semantics are strict:
  - `draft` during creation/edits
  - `approved` before implementation
  - `documentation` only when code is confirmed to match plan

## Troubleshooting

- User skips approval:
  1. Pause progression and request explicit approval for the current stage.
- Inputs/outputs are vague:
  1. Ask for concrete shapes, types, examples, and failure cases.
  2. Do not proceed to acceptance tests until contracts are specific.
- Acceptance criteria are missing:
  1. Ask the user to provide test flows with inputs and pass/fail rules.
  2. Keep stage 3 open until flows are documented.
- User-provided flows are incomplete:
  1. Propose missing flows that should be tested and explain why.
  2. Ask the user to confirm which recommended flows to include in stage 3.
- Pseudocode is unnecessary:
  1. Mark stage 4 as skipped with a short reason.
  2. Continue to stage 5.

## Template

Use `templates/plan-template.md` as the required scaffold for all new plans.
