# /dark-factory:plan

Plans a feature end-to-end — walks through system intent, architecture diagram, and per-flow approval gates, then saves the approved plan (no code yet).

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:plan<br/>taskDescription, taskName"] --> PCA

  PCA["plan-command-agent<br/>(runs in-place)"]

  PCA --> FA["feature-agent<br/>(planOnly: true)"]

  FA -->|"status: question"| PCA
  PCA -->|"AskUserQuestion"| User
  User -->|"answer"| PCA
  PCA -->|"re-invoke"| FA

  FA -->|"status: done"| Done["Done: planPath"]
```

## See also

- feature-agent — executes planning phases
- plan-template.md — plan structure and approval gates
