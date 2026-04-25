---
name: coding-standards
description: Use this skill when writing or reviewing code to ensure it meets naming, commenting, and structural standards.
---
<!-- TODO audit this skill -->

## Required

You must add the following steps to your current task checklist or implementation plan:

1. Review the requirement and verify it is not YAGNI (You Aint Gonna Need It).
2. If using a new library, ask me for approval first.
3. Check that my changes fix ALL failing tests, even if unrelated.
4. Verify naming conventions match the language standards below.

## Context

I adhere to strict coding standards.

- **YAGNI**: I do not add features not explicitly requested.
- **Libraries**: I prefer third-party libraries but always ask before installing.
- **Comments**: I document intent, not process. I delete stale comments.
- **Naming**:
  - Functions: `camelCase` (e.g., `processManifest`)
  - Classes: `PascalCase` (e.g., `EventBuilder`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_EVENTS`)
  - Files: `snake_case` (Python), `kebab-case` (TypeScript)

## Examples

## Good Example

```javascript
// Intent: Throttle events to prevent DB overload
const MAX_EVENTS = 100;

class EventBuilder {
    processManifest() { ... }
}
```

## Bad Example

```javascript
// I added this function to handle events
// version 2.0
const max_events = 100;

class event_builder {
    ProcessManifest() { ... }
}
```
