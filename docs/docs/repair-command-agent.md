# /dark-factory:repair

Applies a small targeted change — no plan required, runs tests in a loop until green, opens a PR.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:repair<br/>taskDescription, taskName"] --> RCA

  RCA["repair-command-agent<br/>(runs in-place)"]

  RCA --> RA["repair-agent<br/>(taskDescription)"]

  RA -->|"success: true"| CRO["code-review-orchestrator-agent"]

  CRO --> UDA["update-documentation-agent"]
  UDA --> SUA["skill-update-agent<br/>(non-fatal)"]
  SUA --> PRA["pr-agent<br/>(new or existing)"]
  PRA -->|"prUrl"| Done["Done: PR URL"]
```

## See also

- [repair-agent](repair-agent.md) — applies targeted fixes with iterative testing
- [code-review-orchestrator-agent](code-review-orchestrator-agent.md) — reviews code changes
- pr-agent — opens/updates PR
