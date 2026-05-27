# /dark-factory:execute

Implements an approved plan — runs the full execution pipeline (code, tests, review) and opens a PR.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:execute<br/>planPath, taskName"] --> ECA

  ECA["execute-command-agent<br/>(runs in-place)"]

  ECA --> EA["execution-agent<br/>(planPath)"]

  EA -->|"success"| CRO["code-review-orchestrator-agent"]

  CRO --> UDA["update-documentation-agent"]
  UDA --> SUA["skill-update-agent<br/>(non-fatal)"]
  SUA --> PRA["pr-agent"]
  PRA -->|"prUrl"| Done["Done: PR URL"]
```

## See also

- execution-agent — implements flows from plan
- [code-review-orchestrator-agent](code-review-orchestrator-agent.md) — reviews code changes
- pr-agent — opens/updates PR
