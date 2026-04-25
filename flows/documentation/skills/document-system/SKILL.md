---
name: document-system
description: Documents an existing system by exploring the codebase and writing a structured system document using the new-plan template format. Use when you need to understand a flow before generating test/debug scripts for it.
user-invocable: false
---

# document-system

Document an existing system by exploring the codebase and filling in the new-plan template. This describes what already exists — not what to build.

## Steps

1. Explore the codebase thoroughly for the given flow:
   - Find the entry point (Lambda handler, route, CLI command, etc.)
   - Trace all components, services, and data stores involved
   - Identify log sources and how to access them
   - Identify how the flow is triggered
   - Identify the terminal states (success and failure signals)
   - Identify how code is deployed for this flow

2. Create a Mermaid diagram of the system:
   - Follow the mermaid diagram skill conventions
   - Include all components, boundaries, and labeled data flows
   - Color nodes by type: external services gray, application code green
   - Every edge must have a label describing what flows between nodes

3. Write the system document using the new-plan template structure:

```markdown
# <flow-name> — System Document

## System Intent

- **What this is**: <one sentence description of what this flow does>
- **Entry point**: <how the flow is triggered>
- **Terminal states**: <what success looks like, what failure looks like>
- **Log sources**: <where logs live for this flow>
- **Deploy mechanism**: <how code is deployed, or "local only">

## Mermaid Diagram

<mermaid diagram here>

## Components

For each component in the flow:

### <component-name>
- **File/location**: <path>
- **Job**: <what it does>
- **Inputs**: <what it receives>
- **Outputs**: <what it produces or writes>

## Failure Modes

| Failure | Where it appears in logs | Terminal signal |
|---------|--------------------------|-----------------|
| <failure type> | <log pattern> | <how to detect it> |
```

4. Write the completed document to `/tmp/system-diagram.md`.
