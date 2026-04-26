---
name: logging
description: "Instruments code flows with structured logs. Adds a log statement at each step of every flow using the format: flow | step | data."
user-invocable: true
---

# Logging

Instruments flows with consistent, machine-readable log statements that can be parsed later for debugging.

## Log Format

```
log<flow><step><data>
```

```js
// JavaScript
console.log("login", "submit", { username })
console.log("login", "response", { status, userId })
```

```python
# Python
logger.info("login", "submit", {"username": username})
logger.info("login", "response", {"status": status, "user_id": user_id})
```

## Steps

### 1. Identify the source file

Accept a path to a plan (`docs/plans/`), bug (`docs/bugs/`), or doc (`docs/docs/`) file. If none is provided, ask for one before proceeding.

### 2. Build a flow checklist

Read the source file and extract every flow. Write a checklist to `tmp/logging-checklist.md` using `skills/logging/templates/logging-checklist-template.md`:

- Set `{{PLAN_BUG_DOC}}` to the path of the plan/bug/doc file
- Set `{{FLOW_ROWS}}` to one row per flow: `| <flow-name> | <file> | [ ] |`
- Leave `{{LOG_STATEMENTS}}` empty for now

### 3. Add logs to each flow

For each flow in the checklist:
1. Open the implementation file
2. Add a log at each meaningful step (entry, branch, error, exit)
3. Use the flow name from the doc as the first argument — keep it consistent across all log calls in that flow
4. Include the most relevant in-scope variables as the data argument
5. Append each added log statement to `{{LOG_STATEMENTS}}` in the checklist
6. Mark the flow row as done (`[x]`)

### 4. Cleanup

Delete `tmp/logging-checklist.md` after all flows are instrumented.

## Notes

- Use the existing logger for the project (`console.log`, `logger.info`, Python `logging`, etc.) — do not introduce a new dependency.
- Keep log messages lowercase and consistent with existing style in the file.
- Do not log sensitive data (passwords, tokens, PII).
