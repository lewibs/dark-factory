# Skills Factory

TODO update this to have all the top level agents and skills for the orchestrators 

You are the orchestrator of this skills factory. Your job is to route work to the correct agent or skill. Always prefer an agent or skill over doing the work yourself.

## Agents

| Agent | Description |
|---|---|
| `fix-flow-orchestrator` | End-to-end: understands a broken integration flow, generates scripts, loops debug → fix → PR → deploy until green. Entry point for fixing a broken flow. |
| `debugger-agent` | Triggers an integration flow, waits for it, fetches logs, and produces a code fix. Does not open PRs. |
| `investigation-agent` | Explores a codebase and writes a structured system document to `/tmp/
| `pr-agent` | Opens a PR, watches CI, resolves review threads, squash-merges, deletes the branch, and returns to main. Use after a fix is applied. |
| `planning-agent` | Works with the user at a high level to design architecture before implementation. Produces a staged plan (Mermaid → I/O contracts → acceptance criteria → pseudocode) in `docs/plans/`. Can invoke `investigation-agent` to research existing systems. |

## Skills

| Skill | Description |
|---|---|
| `systematic-debugging` | Structured debugging workflow for non-obvious bugs. Produces a deduplicated audit log in `docs/bugs`. |
| `create-mermaid-diagram` | Creates or updates Mermaid diagrams for code changes. |
