---
name: task-classifier
description: "Classifies a task description into one of three work routes (feature, debugger, repair) using signal matching. Returns classification string or asks clarifying question on ambiguity."
user-invocable: false
---

# task-classifier

Classify a task description to determine which worker agent should be invoked.

## Input

- `taskDescription` — the user's task request (string)

## Output

Returns a JSON object with one of two structures:

### Classification Result (no ambiguity)
```json
{
  "classification": "feature" | "debugger" | "repair",
  "ambiguous": false,
  "signal": "matched signal text",
  "confidence": 0.9
}
```

### Ambiguity (no clear match)
```json
{
  "classification": null,
  "ambiguous": true,
  "question": "Is this a new feature or a bug fix?",
  "options": [
    { "label": "New Feature", "value": "feature" },
    { "label": "Bug Fix", "value": "debugger" },
    { "label": "Small Change / Tweak", "value": "repair" }
  ]
}
```

## Classification Guidelines

Use judgment to route based on the *intent and scope* of the task, not keyword matching.

### feature
Route here if a reasonable engineer would want to design this before building it. This includes:
- Any new artifact (command, skill, agent, script, system)
- Significant behavior changes or additions
- Refactors that touch multiple files or systems
- Anything where getting it wrong would waste a lot of time

When in doubt between `feature` and `repair`, route to `feature`. Planning is cheap; rework is not.

### repair
Route here only if the task is small, targeted, and self-contained — the kind of thing you'd do without a design doc. Single-file changes, renames, typo fixes, minor tweaks.

### debugger
Route here if the task is about diagnosing and fixing a bug, crash, or unexpected behavior. The symptom is clear but the root cause isn't.

### ambiguous
If you genuinely cannot tell — e.g. "fix the auth stuff" could be a bug or a refactor — return the ambiguous structure and ask the user to clarify.

## Rules

- Use intent and scope, not keywords
- Prefer `feature` over `repair` when scope is uncertain
- Only use `ambiguous` when you truly cannot determine intent — do not use it as a default
