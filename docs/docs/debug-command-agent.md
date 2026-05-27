# /dark-factory:debug

Diagnoses and fixes a non-obvious bug — fills out a bug audit log, applies the fix, and opens a PR.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:debug<br/>taskDescription, taskName"] --> DCA

  DCA["debug-command-agent<br/>(runs in-place)"]

  DCA --> DA["debugger-agent<br/>(taskDescription)"]

  DA -->|"success"| CRO["code-review-orchestrator-agent"]

  CRO --> UDA["update-documentation-agent"]
  UDA --> SUA["skill-update-agent<br/>(non-fatal)"]
  SUA --> PRA["pr-agent"]
  PRA -->|"prUrl"| Done["Done: PR URL"]
```

## See also

- [debugger-agent](debugger-agent.md) — investigates and fixes bugs
- bug-audit-log-template.md — structured bug documentation
- [code-review-orchestrator-agent](code-review-orchestrator-agent.md) — reviews code changes
