# Commands

## Metadata

- System type: `library`
- Owner: dark-factory plugin
- Source directory: `commands/`
- Command count: 2 slash commands

## System Intent

- What this is: The `commands/` directory contains the two Claude Code slash commands that Dark Factory exposes to the developer. Each command file is a minimal markdown stub that delegates all logic to the corresponding orchestrator agent or runs inline shell commands. Commands carry a `description` field for the Claude Code command picker and a delegation line or inline commands in the body.
- Primary consumer(s): Developers invoking slash commands from the Claude Code interface.
- Boundary: Commands only contain front-matter and a delegation line. All orchestration logic lives in `agents/`.

## Mermaid Diagram

```mermaid
flowchart TD
  Dev([Developer]) -->|/dark-factory:manufacture task| CMD_M[commands/manufacture.md]
  Dev -->|/dark-factory:install| CMD_I[commands/install.md]

  CMD_M -->|delegates to| DFA[agents/dark-factory/agents/dark-factory-agent.md]
  CMD_I -->|runs directly| GIT[git pull + claude plugin marketplace add/update/uninstall/install]
```

## Flows

### Flow: `manufacture`

- Core files: `commands/manufacture.md`, `agents/dark-factory/agents/dark-factory-agent.md`

#### Types

```txt
ManufactureInput {
  taskDescription: string (free-text, e.g. "add OAuth login", "fix login crash")
}

ManufactureOutput {
  prUrl: string
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `manufacture.success` | `ManufactureInput` | `ManufactureOutput` | `happy path` | Delegates to dark-factory-agent; routes feature/debug/fix-flow, reviews, opens PR |
| `manufacture.error` | `ManufactureInput` | `StandardError` | `error` | Worker agent returns error or hard-stop; cleanup runs |

---

### Flow: `install`

- Core files: `commands/install.md`

#### Types

```txt
InstallInput {
  void (no arguments; run from repo root)
}

InstallOutput {
  void (outputs plugin reinstall progress to terminal)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `install.success` | `InstallInput` | `InstallOutput` | `happy path` | Runs `git pull`, `claude plugin marketplace add "$(pwd)"`, `claude plugin marketplace update dark-factory`, `claude plugin uninstall "dark-factory@dark-factory"`, `claude plugin install "dark-factory@dark-factory"`, `bash scripts/reopen-remote-control.sh "dark factory"` |

## Logs

| Source | Location |
|--------|----------|
| N/A | Commands are thin stubs; they produce no structured log output. Terminal output from `git pull` and `claude plugin install` is the only observable output for the install command. |

## Deployment

- Mechanism: `local only`
- Deploy command:
  ```bash
  # Commands become available after installing the plugin:
  claude plugin install dark-factory
  # Commands are then accessible as /dark-factory:<name> in the Claude Code interface.
  ```
- Notes: Commands are loaded by the Claude Code runtime from the plugin's `commands/` directory. No deployment step beyond plugin installation.
