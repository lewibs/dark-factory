---
name: manage-learnings
description: Use this skill to migrate new learnings into the relevant skill files and keep skills current.
---

## Required

You must add the following steps to your current task checklist or implementation plan:

1. Identify the most relevant skill for each new learning.
2. Update the target skill's **Required** or **Context** section with concise, actionable guidance.
3. Keep `LEARNINGS.md` as a pointer only (no new entries).
4. Remove or merge duplicate guidance across skills to avoid drift.

## Context

I encode learnings in skills so they directly shape workflow.

- **Scope**: Actionable, repeatable rules that change how work is done.
- **Placement**:
  - Use **Required** for mandatory steps.
  - Use **Context** for invariant guidance.
- **Avoid**: One-off fixes, long narratives, or evidence dumps in skills.

## Examples

## Good Example

Add to `manage-infrastructure` **Context**:

- **DynamoDB**: Use `BILLING_MODE = PAY_PER_REQUEST` to avoid idle cost.

## Bad Example

### Added a one-off fix to a skill

- Avoid one-off fixes. Only add reusable rules to skills.
