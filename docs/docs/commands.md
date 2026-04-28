# Commands

## Metadata

- System type: `library`
- Owner: dark-factory plugin
- Source directory: `commands/`
- Command count: 4 slash commands

## System Intent

- What this is: The `commands/` directory contains the four Claude Code slash commands that Dark Factory exposes to the developer. Each command file is a minimal markdown stub that delegates all logic to the corresponding orchestrator agent or runs inline shell commands. Commands carry a `description` field for the Claude Code command picker and a delegation line or inline commands in the body.
- Primary consumer(s): Developers invoking slash commands from the Claude Code interface.
- Boundary: Commands only contain front-matter and a delegation line. All orchestration logic lives in `agents/`.

## Mermaid Diagram

```mermaid
flowchart TD
  Dev([Developer]) -->|/dark-factory:manufacture task| CMD_M[commands/manufacture.md]
  Dev -->|/dark-factory:spawn-factory| CMD_S[commands/spawn-factory.md]
  Dev -->|/dark-factory:install| CMD_I[commands/install.md]
  Dev -->|/dark-factory:destroy-factories| CMD_D[commands/destroy-factories.md]

  CMD_M -->|delegates to| DFA[agents/dark-factory/agents/dark-factory-agent.md]
  CMD_S -->|launches| TERM[New gnome-terminal running claude /remote-control]
  CMD_I -->|runs directly| GIT[git pull + claude plugin marketplace add/update/uninstall/install]
  CMD_D -->|bash scripts/destroy-factories.sh| DS[scripts/destroy-factories.sh kills Claude terminals, spawns fresh one]
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

### Flow: `spawn-factory`

- Core files: `commands/spawn-factory.md`

#### Types

```txt
SpawnFactoryInput {
  terminalName: string (optional, defaults to "dark factory")
}

SpawnFactoryOutput {
  status: "success" | "error"
  message: string (status message or error description)
}

StandardError {
  message: string (human-readable description of what went wrong)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `spawn-factory.success` | `SpawnFactoryInput` | `SpawnFactoryOutput{status: success}` | `happy path` | New gnome-terminal launched with `claude /remote-control <name>` in current working directory |
| `spawn-factory.terminal-fail` | `SpawnFactoryInput` | `SpawnFactoryOutput{status: error}` | `error` | gnome-terminal not available or failed to launch |

#### Pseudocode

```
function spawn-factory(terminalName):
  name = terminalName ?? "dark factory"
  workdir = current working directory
  execute_async:
    gnome-terminal --working-directory=workdir -- bash -c "claude /remote-control <name>"
  return { status: "success", message: "Terminal launched" }
```

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

---

### Flow: `destroy-factories`

- Core files: `commands/destroy-factories.md`, `scripts/destroy-factories.sh`

#### Types

```txt
DestroyFactoriesInput {
  name: string (optional, default: "dark factory" — remote-control session name for the new terminal)
}

DestroyFactoriesOutput {
  void (side effects: all Claude terminals killed, one new factory terminal spawned)
}

StandardError {
  message: string (written to stderr)
}
```

#### Paths

| path | input | output | path-type | notes |
| --- | --- | --- | --- | --- |
| `destroy-factories.success` | `DestroyFactoriesInput` | `DestroyFactoriesOutput` | `happy path` | All Claude terminals found and killed; new factory terminal spawned successfully |
| `destroy-factories.none-found` | `DestroyFactoriesInput` | `DestroyFactoriesOutput` | `happy path` | No other Claude terminals found; new factory terminal spawned (no kills needed) |
| `destroy-factories.kill-failed` | `DestroyFactoriesInput` | `StandardError` | `degraded` | One or more terminals could not be killed (permission error); warns to stderr, continues to spawn |
| `destroy-factories.spawn-failed` | `DestroyFactoriesInput` | `StandardError` | `error` | New terminal could not be opened (no emulator found or emulator returned non-zero); exits non-zero |

## Logs

| Source | Location |
|--------|----------|
| N/A | Commands are thin stubs; they produce no structured log output. Terminal output from `git pull` and `claude plugin install` is the only observable output for the install command. |
| destroy-factories stderr | terminal session running the destroy-factories command (structured logs: `destroy-factories | <flow> | <step> | <data>`) |

## Deployment

- Mechanism: `local only`
- Deploy command:
  ```bash
  # Commands become available after installing the plugin:
  claude plugin install dark-factory
  # Commands are then accessible as /dark-factory:<name> in the Claude Code interface.
  ```
- Notes: Commands are loaded by the Claude Code runtime from the plugin's `commands/` directory. No deployment step beyond plugin installation.
