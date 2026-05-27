# /dark-factory:investigation

Investigates a system and writes authoritative documentation to `docs/docs/` — validates every claim against source code and commits the verified doc.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:investigation<br/>system, question"] --> ORC["investigation-orchestrator"]
  ORC --> IA["investigation-agent"]
  IA -->|"writes docs"| DOC["docs/docs/<system>.md"]
  ORC --> CV["claim-validator-agent"]
  CV -->|"result"| ORC
  ORC -->|"corrections needed?"| IA
  ORC -->|"all verified"| HOOK["git commit<br/>SubagentStop"]
```

## See also

- [investigation-agent](investigation-agent.md) — generates system documentation
- [claim-validator-agent](claim-validator-agent.md) — validates factual claims
