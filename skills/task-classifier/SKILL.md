---
name: task-classifier
description: "Classifies a task description into one of four work routes (feature, fix-flow, debugger, repair) using signal matching. Returns classification string or asks clarifying question on ambiguity."
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
  "classification": "feature" | "fix-flow" | "debugger" | "repair",
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
    { "label": "Broken Flow / End-to-End", "value": "fix-flow" },
    { "label": "Small Change / Tweak", "value": "repair" }
  ]
}
```

## Classification Rules

Match signals in the order listed below — first match wins.

| Signal in taskDescription | Route to | Examples |
|---|---|---|
| "small change", "tweak", "rename", "minor update", "quick fix", "adjust", "alter" | `repair` | "tweak the login button color", "rename AuthProvider to AuthService", "quick fix for typo" |
| "add", "build", "create", "implement", "new feature" | `feature` | "add OAuth support", "create new dashboard widget", "implement dark mode" |
| "broken flow", "integration failing", "end-to-end", "pipeline" | `fix-flow` | "authentication flow is broken", "payment pipeline failing", "end-to-end test broken" |
| "bug", "crash", "error", "fix", "broken", "not working", "debug" | `debugger` | "login button crashes", "fix null pointer error", "database query broken" |
| Ambiguous | Query user | Any task without clear keywords |

## Matching Algorithm

1. Split `taskDescription` into lowercase words
2. For each rule in order:
   - Check if ANY signal phrase appears in the description (substring match, case-insensitive)
   - If match found: return `classification` result with that route
3. If no signals match: return `ambiguous` result with clarification question

## Rules

- Signal phrases are matched as case-insensitive substrings (e.g., "Add" matches "add", "ADD", "Adding")
- First match wins — order matters
- If multiple signals match, use the first rule encountered (e.g., "add" comes before "fix", so "add a fix" routes to feature, not debugger)
- When ambiguous, return the question structure so dark-factory-agent can ask the user and re-classify
