# /dark-factory:save

Commits current changes and opens (or updates) a PR — lightweight shortcut that skips code review, docs, and skills pipeline.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:save<br/>taskDescription (optional)"] --> SCA["save-command-agent"]

  SCA --> PR["pr-agent<br/>(commit + push + PR)"]

  PR -->|"prUrl"| Done["Done: PR URL"]
```

## See also

- pr-agent — commits, pushes, and opens/updates PR
- [/dark-factory:repair](repair-command-agent.md) — for targeted changes that need review and testing
