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
| `execution-agent` | Executes an approved plan file end-to-end: scaffolds skeleton files, writes failing tests, implements flows one at a time until all tests pass. Invokes deviation protocol on plan conflicts. |
| `feature-agent` | Orchestrates end-to-end feature work: invokes planning-agent, gates on human approval (with feedback-and-retry), then invokes execution-agent. |
| `init-orchestrator-agent` | Entry point for setting up a project with dark factory. Runs `init.sh`, generates `CLAUDE.md` via `init-docs-agent`, then opens a PR titled "init: dark factory". |
| `init-docs-agent` | Explores a newly initialized project directory and generates a `CLAUDE.md` at its root. Called by `init-orchestrator-agent`. |

## Scripts

| Script | Description |
|---|---|
| `agents/initialization/scripts/init.sh [github-url]` | Sets up dark-factory project structure. With a URL: `mkdir <repo> && git clone`. Without: reorganizes current dir into `<dirname>/<dirname>/`. |

## Skills

| Skill | Description |
|---|---|
| `systematic-debugging` | Structured debugging workflow for non-obvious bugs. Produces a deduplicated audit log in `docs/bugs`. |
| `create-mermaid-diagram` | Creates or updates Mermaid diagrams for code changes. |
