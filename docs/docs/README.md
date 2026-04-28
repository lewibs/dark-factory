# Documentation Index

| Document | Description |
|---|---|
| [manufacture.md](./manufacture.md) | Top-level orchestration flow: routes a task to the right worker agent, runs code review, updates docs and skills, opens a PR, and cleans up |
| [build-feature.md](./build-feature.md) | End-to-end feature flow: planning with human approval gate, then skeleton → tests → implementation execution |
| [debug-bug.md](./debug-bug.md) | Systematic bug-debugging flow: reproduce, confirm, identify root cause, fix, verify, and write an audit log to docs/bugs/ |
| [fix-broken-flow.md](./fix-broken-flow.md) | Integration-flow repair loop: investigate system, generate trigger/log scripts, then fix-and-push iterations until the flow passes green |
| [open-pr.md](./open-pr.md) | Full PR lifecycle: stage changes, open PR, wait for CI, resolve failures and review threads, squash-merge, and clean up the branch |
| [code-review.md](./code-review.md) | Automated code review: parallel high-level and low-level reviewers feed a resolver loop that runs until all issues are cleared |
| [update-documentation.md](./update-documentation.md) | Post-implementation doc maintenance: identify affected flows, update or create docs/docs/ files to reflect what was built |
| [repair.md](./repair.md) | Lightweight repair flow: targeted fix without planning — implements change, runs tests with up to 5 retries, optionally updates docs, and opens a PR |
| [mermaid-to-image.md](./mermaid-to-image.md) | Script that extracts a Mermaid block from a plan file, base64-encodes it, and returns a mermaid.ink URL; called by planning-agent to push a tappable diagram link to the developer's phone |
