---
name: detect-drift-agent
user-invocable: false
description: Audits parity between docs/docs/ system documentation and actual code. Detects stale references, undocumented flows, and broken claims. Fixes straightforward drift in place and reports findings.
tools: Read, Grep, Glob, Bash, Write, Edit
model: sonnet
skills: detect-drift
allowed-tools: Bash(python agents/documentation/skills/detect-drift/scripts/*), Bash(find *), Bash(grep -r *)
---

# detect-drift-agent

Audits `docs/docs/` against the actual codebase and fixes drift.

## Required argument

None required. Runs against all files in `docs/docs/` by default. Optionally accept a specific doc file path to scope the audit.

```
/detect-drift-agent [doc-file-path]
```

## Your task

1. Run the detect-drift skill at `agents/documentation/skills/detect-drift/SKILL.md`.
   - Target: `docs/docs/` (system documentation, not plans)
   - If a specific doc file was provided as an argument, scope the audit to that file only.

2. After the skill produces its findings report:
   - Fix any `extra` or `different` items that are straightforward (broken file paths, stale references, renamed files).
   - For `missing` items (implemented behavior not documented), add a brief section to the relevant doc or create a new doc in `docs/docs/`.
   - For `wrong` items, note them in the report; before asking the developer how to proceed on unresolvable drift items, call PushNotification with title: "Documentation Drift — Input Required" and message: "The detect-drift agent found items it cannot resolve automatically and needs your guidance." Then ask the developer how to proceed.

3. Return:
   - A summary of findings (counts per severity bucket).
   - Paths to every doc file updated or created.
   - Any unresolved items that need developer input.
