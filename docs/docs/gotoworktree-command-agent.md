# /dark-factory:goto

Finds or creates a git worktree for a PR, branch, or new task — pulls main/master and reports the path.

## Flow

```mermaid
flowchart TD
  User["User: /dark-factory:goto<br/>prNumber, taskName, or description"] --> GW

  GW["gotoworktree-command-agent"]

  GW --> LOCAL{"Local worktree<br/>exists?"}
  LOCAL -->|"yes"| PULL["git pull origin main/master"]
  PULL --> DONE["Report: Worktree ready"]

  LOCAL -->|"no"| PR_CHK{"Open PR<br/>found?"}
  PR_CHK -->|"yes"| CREATE["git worktree add"]
  CREATE --> PULL

  PR_CHK -->|"no"| PREP["prep-feature-dir.sh"]
  PREP --> PULL
```

## See also

- [find-related-pr](find-related-pr.md) — searches for matching open PRs
- prep-feature-dir.sh — creates new worktree
