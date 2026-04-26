# Dark Factory

Dark Factory is a fully autonomous coding plugin for Claude Code. It is a Claude Code plugin that orchestrates end-to-end software development tasks — building features, fixing bugs, and repairing broken integration flows — without requiring human intervention beyond initial task description and plan approval. It is designed for developers who want to delegate entire units of work (design, implement, code review, PR, and cleanup) to an AI agent pipeline.

## Architecture

Dark Factory is structured as a Claude Code plugin composed of hierarchical agents, skills, and slash commands. The top-level `manufacture` command routes work to specialized worker agents (feature, debugger, or fix-flow), each of which may invoke further sub-agents. All agents are defined as Markdown files with YAML front-matter that Claude Code interprets directly. There is no traditional application runtime — the "code" is the agent instruction set.

### Primary directories

| Directory | Role |
|---|---|
| `commands/` | Slash command entry points (`manufacture.md`, `init.md`, `update.md`) registered with Claude Code |
| `agents/` | All agent definitions organized by domain |
| `agents/dark-factory/` | Top-level orchestrator agent and the `prep-feature-dir.sh` isolation script |
| `agents/featurework/` | Feature pipeline: `feature-agent`, `planning-agent`, `execution-agent`, `skeleton-agent`, `testing-agent`, `implementation-agent` |
| `agents/fix-flow/` | Integration-fix pipeline: `fix-flow-orchestrator`, `setup-wizard`, `debug-flow-agent`, `ralph-fix-and-push` |
| `agents/debugger/` | Bug diagnosis: `debugger-agent` and its `debug` skill |
| `agents/code-review/` | Automated code review: `code-review-orchestrator-agent`, `high-level-review-agent`, `low-level-review-agent`, `resolver-agent` |
| `agents/pr/` | Full PR lifecycle: `pr-agent`, `resolve-pr-issue`, `create-pr` skill |
| `agents/initialization/` | Project onboarding: `init-orchestrator-agent`, `init-docs-agent`, `init.sh` |
| `agents/documentation/` | Documentation hygiene: `investigation-agent`, `update-documentation-agent`, `detect-drift-agent` |
| `agents/skill-update/` | Learns from completed work: `skill-update-agent` writes or updates skills in the target project's `skills/` directory |
| `skills/` | Reusable shared skills: `create-mermaid-diagram`, `find-dead-code`, `install`, `install-plugin`, `logging`, `open-in-vscode` |
| `.claude-plugin/` | Plugin metadata (`plugin.json`, `marketplace.json`) consumed by `claude plugin` CLI |
| `.claude/` | Claude Code settings (`settings.json`, `settings.local.json`) granting allowed bash commands |
| `docs/` | Runtime-generated documentation (plans in `docs/plans/`, bug audits in `docs/bugs/`, system docs in `docs/docs/`) |

## Key Entry Points

| File | Purpose |
|---|---|
| `commands/manufacture.md` | Slash command `/dark-factory:manufacture` — delegates to `dark-factory-agent` to run a full task end-to-end |
| `commands/init.md` | Slash command `/dark-factory:init` — delegates to `init-orchestrator-agent` to onboard a project |
| `commands/update.md` | Slash command `/dark-factory:update` — runs `git pull` and `claude plugin update` |
| `agents/dark-factory/agents/dark-factory-agent.md` | Top-level orchestrator: prepares an isolated work dir, routes to the right worker (feature/debugger/fix-flow), runs code review, updates docs, writes skills, opens PR, and cleans up |
| `agents/featurework/agents/feature-agent.md` | Feature pipeline orchestrator: planning → human approval gate → execution |
| `agents/featurework/planning/agents/planning-agent.md` | Produces a staged plan (Mermaid → I/O contracts → acceptance criteria → pseudocode) in `docs/plans/` |
| `agents/featurework/execution/agents/execution-agent.md` | Executes an approved plan file: scaffolds skeleton, writes failing tests, implements until all pass |
| `agents/fix-flow/agents/fix-flow-orchestrator.md` | Autonomously repairs a broken integration flow: investigate → setup scripts → loop debug/fix/PR/deploy |
| `agents/debugger/agents/debugger-agent.md` | Diagnoses bugs, triggers flows, fetches logs, produces a code fix (does not open PRs itself) |
| `agents/code-review/agents/code-review-orchestrator-agent.md` | Spawns high-level and low-level reviewers in parallel, then loops a resolver until all issues are clear |
| `agents/pr/agents/pr-agent.md` | Opens PR, monitors CI, resolves review threads, squash-merges, deletes branch, returns to main |
| `agents/initialization/agents/init-orchestrator-agent.md` | Runs `init.sh`, generates `CLAUDE.md` via `init-docs-agent`, opens a PR titled "init: dark factory" |
| `agents/initialization/scripts/init.sh` | Bash script that sets up the two-level directory structure (`<repo>/<repo>/`) required by dark factory |
| `agents/dark-factory/scripts/prep-feature-dir.sh` | Bash script that clones the inner project into an isolated work dir (`dark_factory-<task-name>/`) for each task |
| `.claude-plugin/plugin.json` | Plugin manifest (name, version, commands path, skills paths) read by `claude plugin install` |

## Development

Dark Factory has no build step, no compiled output, and no package manager. All agent logic lives in Markdown files.

**Install as a Claude Code plugin:**

```sh
git clone https://github.com/lewibs/dark-factory
cd dark-factory
claude plugin marketplace add "$(pwd)"
claude plugin install dark-factory
```

**Verify installation:**

```sh
claude plugin list
```

**Update to latest:**

```sh
/dark-factory:update
```

Or manually:

```sh
git pull
claude plugin update "dark-factory@dark-factory"
```

There are no automated tests in this repository. Agent correctness is validated by running the plugin against real tasks.

## Deploy

This plugin is distributed via `claude plugin` — there is no server deployment. Publishing a new version means pushing to the GitHub repository (`https://github.com/lewibs/dark-factory`) and incrementing the version in `.claude-plugin/plugin.json`. Users update by running `/dark-factory:update` or the equivalent `git pull && claude plugin update` commands.

## Notes

- **Two-level directory structure**: Dark Factory expects projects to be laid out as `<wrapper>/<project>/` (e.g., `dark_factory/dark_factory/`). `init.sh` enforces this. The `prep-feature-dir.sh` script copies the inner directory into an isolated work dir (`dark_factory-<task-name>/`) sibling to `dark_factory/` so each task runs in isolation.
- **Agents never write code directly**: every agent delegates to sub-agents or skills. The `dark-factory-agent`, `feature-agent`, and `fix-flow-orchestrator` are pure orchestrators.
- **Plan approval gate**: for feature work, `feature-agent` always pauses to show the plan and wait for a human "yes/approve" before invoking `execution-agent`. Reply "abort" to cancel, or provide feedback to trigger a revision loop.
- **Skill accumulation**: after each successful manufacture run, `skill-update-agent` inspects the completed work and may write new `SKILL.md` files into the target project's `skills/` directory so future runs can reuse discovered patterns.
- **PR agent uses `git add --all`**: every file changed during a task (including generated docs and skill files) is staged automatically.
- **Allowed tools**: `.claude/settings.json` pre-approves a broad set of bash commands (git, gh, bash, python, node, standard Unix utilities). Additional per-agent restrictions are declared in each agent's YAML front-matter `allowed-tools` field.
- **`/tmp/` is the only writable scratch space** granted globally; agents that need temporary files write there.
- **`docs/` is ephemeral per work dir**: plans go to `docs/plans/`, bug audit logs to `docs/bugs/`, and system investigation docs to `docs/docs/`. These persist in the PR as project documentation.
