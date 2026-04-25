# fix-flow-orchestrator Plugin

## Plan Metadata

- Plan type: `plan`
- Parent plan: N/A
- Depends on: N/A (fully self-contained)
- Status: `approved`

Status semantics:
- `draft`: Plan is being created or updated and is not final.
- `approved`: Plan is approved but not yet applied in code.
- `documentation`: Code currently exists and matches the plan contract.

Update rule:
- When an existing plan is edited, set status to `draft` until re-approved.

## System Intent

- **What is being built**: A fully self-contained Claude Code skill (`/fix-flow-orchestrator`) with its own internal sub-skills, scripts, and orchestration. A parent skill manages a tight ralph-fix-and-push — spawning a fresh sub-agent per iteration to run the integration command, parse errors, debug, fix, and open a PR — until the command passes green.
- **Primary consumer(s)**: Developers who want to autonomously drive a failing integration flow to green without manual debug iterations.
- **Boundary (black-box scope only)**: Accepts a shell command + repo context; emits a passing test run and one or more open PRs containing fixes. No external skill dependencies.

## Stage Gate Tracker

- [x] Stage 1 Mermaid approved
- [x] Stage 2 I/O contracts approved
- [x] Stage 3 pseudocode/technical details approved or skipped — skipped, contracts are sufficient

---

## 1. Mermaid Diagram

Reference: `.agent/skills/create-mermaid-diagram/SKILL.md`

```mermaid
flowchart TD
  User([Developer]):::unchanged

  subgraph Plugin["fix-flow-orchestrator — SKILL.md owns all phases"]
    A[SKILL.md\n~/github/skills/fix-flow-orchestrator/SKILL.md]:::created
  end

  subgraph Understand["Phase 1 — understand-agent — spawned once, gates Phase 2"]
    UA[understand-agent.md\n~/github/skills/fix-flow-orchestrator/understand-agent.md]:::created

    subgraph UnderstandSkills["skills/ — used by understand-agent"]
      U2[document-system.md\nskills/document-system.md]:::created
    end

    UA -->|invoke document-system.md| U2
  end

  subgraph Wizard["Phase 2 — setup-wizard — sub-orchestrator"]
    W[setup-wizard.md\n~/github/skills/fix-flow-orchestrator/setup-wizard.md]:::created

    subgraph SetupSkills["setup-skills/ — one skill per generated script"]
      W2[generate-trigger.md\nsetup-skills/generate-trigger.md]:::created
      W3[generate-wait-for-completion.md\nsetup-skills/generate-wait-for-completion.md]:::created
      W4[generate-fetch-logs.md\nsetup-skills/generate-fetch-logs.md]:::created
      W5[generate-deploy.md\nsetup-skills/generate-deploy.md — OPTIONAL]:::created
      W2 -->|system doc| W3 -->|system doc| W4 -->|system doc| W5
    end

    W -->|passes system doc| W2
  end

  subgraph RalphFixAndPush["Phase 3 — ralph-fix-and-push — owns the loop"]
    R[ralph-fix-and-push.md\n~/github/skills/fix-flow-orchestrator/ralph-fix-and-push.md]:::created

    subgraph Debugger["debugger-agent — spawned per iteration"]
      DA[debugger-agent.md\n~/github/skills/fix-flow-orchestrator/debugger-agent.md]:::created

      subgraph Scripts["generated scripts — called by debugger-agent"]
        C[trigger.sh]:::created
        WC[wait-for-completion.sh]:::created
        D[fetch-logs.sh]:::created
        DEP[deploy.sh — OPTIONAL]:::created
      end

      subgraph DebugSkills["skills/ — used by debugger-agent"]
        E[debug.md\nskills/debug.md]:::created
      end
    end

    subgraph PRAgent["pr-agent — spawned after each fix"]
      PA[pr-agent.md\n~/github/skills/fix-flow-orchestrator/pr-agent.md]:::created

      subgraph PRSkills["skills/ — used by pr-agent"]
        F[create-pr.md\nskills/create-pr.md]:::created
      end
    end
  end

  GH([GitHub\nexternal]):::unchanged
  ENV([Prod/Staging env\nexternal]):::unchanged

  User -->|invokes with required flow name| A
  A -->|Phase 1 — spawn understand-agent| UA
  U2 -->|/tmp/system-diagram.md| UA
  UA -->|gates Phase 2| A
  A -->|Phase 2 — spawn setup-wizard| W
  A -->|passes /tmp/system-diagram.md| W
  W5 -->|script paths| A
  A -->|Phase 3 — spawn ralph-fix-and-push with script paths| R
  R -->|spawn debugger-agent| DA
  DA -->|run trigger.sh| C
  C -->|fire flow| ENV
  DA -->|run wait-for-completion.sh| WC
  WC -->|poll until terminal state| ENV
  WC -->|terminal: success or failure| DA
  DA -->|run fetch-logs.sh| D
  D -->|raw logs| DA
  DA -->|invoke debug.md| E
  E -->|bug file + fix diff| DA
  DA -->|bug writeup + fix diff| R
  R -->|spawn pr-agent with fix| PA
  PA -->|invoke create-pr.md| F
  F -->|open PR| GH
  PA -->|wait for CI + address comments| GH
  GH -->|CI green + comments resolved| PA
  PA -->|auto-merge| GH
  PA -->|merged — pr_url| R
  R -->|run deploy.sh if needed| DEP
  DEP -->|fix live| ENV
  R -->|spawn debugger-agent again| DA
  DA -->|flow green — exit_code 0| R
  R -->|all-green + pr_urls| A
  A -->|all-green| User

classDef unchanged fill:#d3d3d3,stroke:#666,stroke-width:1px;
classDef created fill:#a8e6a3,stroke:#666,stroke-width:1px;
```

**Node path notes:**
- All files live under `~/github/skills/fix-flow-orchestrator/`.
- `understand-agent.md` is a dedicated sub-agent spawned once for Phase 1 — the orchestrator never does the understanding work itself.
- `skills/document-system.md` mirrors the new-plan template exactly — Mermaid diagram, I/O contracts, component descriptions — but documents an existing system by reading the code rather than planning new work.
- Phase 1 gates Phase 2: setup-wizard only runs after `understand-agent` writes `/tmp/system-diagram.md`.
- `/tmp/system-diagram.md` is a temporary working file — the orchestrator deletes it when the session ends.
- `setup-skills/` contains one skill per generated script.
- `ralph-fix-and-push.md` owns Phase 3 entirely — the orchestrator spawns it and only gets back `{ all_green, pr_urls }`.
- `skills/debug.md` is used by the debugger-agent only.
- `skills/create-pr.md` is used by the pr-agent only.
- Neither the orchestrator nor ralph-fix-and-push ever touch GitHub directly — only pr-agent does.
- `scripts/` is where generated scripts land: `trigger.sh`, `wait-for-completion.sh`, `fetch-logs.sh`, `deploy.sh` (optional).

---

## 2. Black-Box Inputs and Outputs

### `SKILL.md` — orchestrator

**Job:** Entry point. Runs Phase 1, Phase 2, then Phase 3 in strict sequence. Holds `/tmp/system-diagram.md` for the duration of the session and cleans it up on exit. Does not know about the internal workings of any phase.

| | Description |
|---|---|
| **In** | Developer invocation with required flow argument — e.g. `/fix-flow-orchestrator ingest_window` |
| **Out** | All-green confirmation + list of PR URLs created across iterations; cleans up `/tmp/system-diagram.md` on exit |

---

### Phase 1 — Understand System

#### `understand-agent.md`

**Job:** Spawned once. Explores the codebase and writes the system document. Returns when `/tmp/system-diagram.md` is written — that file gates Phase 2.

| | Description |
|---|---|
| **In** | Flow name from orchestrator |
| **Invokes** | `skills/document-system.md` |
| **Out** | `/tmp/system-diagram.md` written to disk |

#### `skills/document-system.md`

**Job:** Explores the codebase and documents the existing system using the new-plan template — Mermaid diagram, I/O contracts, component descriptions. Describes what already exists, not what to build.

| | Description |
|---|---|
| **In** | Flow name |
| **Out** | `/tmp/system-diagram.md` — structured identically to a new-plan file |

---

### Phase 2 — Setup

#### `setup-wizard.md`

**Job:** Reads `/tmp/system-diagram.md` and orchestrates each setup sub-skill in sequence to generate the scripts the ralph-fix-and-push needs.

| | Description |
|---|---|
| **In** | `/tmp/system-diagram.md` from orchestrator |
| **Out** | Paths to all generated scripts, passed back to SKILL.md |
| **Invokes** | `generate-trigger.md` → `generate-wait-for-completion.md` → `generate-fetch-logs.md` → `generate-deploy.md` (optional) |

#### `setup-skills/generate-trigger.md`

| | Description |
|---|---|
| **In** | `/tmp/system-diagram.md` |
| **Out** | `scripts/trigger.sh` — fires the flow and exits immediately |

#### `setup-skills/generate-wait-for-completion.md`

| | Description |
|---|---|
| **In** | `/tmp/system-diagram.md` |
| **Out** | `scripts/wait-for-completion.sh` — polls until success (exit 0) or failure (exit 1) |

#### `setup-skills/generate-fetch-logs.md`

| | Description |
|---|---|
| **In** | `/tmp/system-diagram.md` |
| **Out** | `scripts/fetch-logs.sh` — fetches all relevant logs and prints to stdout |

#### `setup-skills/generate-deploy.md` _(optional)_

| | Description |
|---|---|
| **In** | `/tmp/system-diagram.md` |
| **Out** | `scripts/deploy.sh` — deploys current code to target environment; exits 0 on success |

---

### Phase 3 — Ralph Fix and Push

#### `ralph-fix-and-push.md` — loop controller

**Job:** Spawned by the orchestrator with the generated script paths. Owns the entire loop — spawns debugger-agent, receives `/tmp/bug-explanation.md` path back, passes it to pr-agent, handles deploy if needed, repeats until the flow passes. The orchestrator knows nothing about what happens inside.

| | Description |
|---|---|
| **In** | Script paths from orchestrator |
| **Out** | `{ all_green: true, pr_urls: [] }` — returned to orchestrator |

#### `debugger-agent.md` — spawned per iteration by ralph-fix-and-push

**Job:** Run the flow, wait for it to finish, fetch logs, and produce a fix. Does not touch GitHub — hands the fix back to the orchestrator.

| | Description |
|---|---|
| **In** | Paths to generated scripts + iteration number |
| **Calls** | `trigger.sh` → `wait-for-completion.sh` → `fetch-logs.sh` → `debug.md` |
| **Out** | `/tmp/bug-explanation.md` path + fix applied to working tree — returned to ralph-fix-and-push |

#### `skills/debug.md`

**Job:** Read raw logs, identify root cause, write a bug explanation, apply a code fix. The bug explanation is used as the PR summary/description.

| | Description |
|---|---|
| **In** | Raw log output from `fetch-logs.sh` + flow context |
| **Out** | Bug explanation written to `/tmp/bug-explanation.md` + fix applied to working tree |

#### `pr-agent.md` — spawned after each fix by ralph-fix-and-push

**Job:** Own the full PR lifecycle. Receives the bug explanation path from ralph-fix-and-push, reads it, and uses it as the PR description. Creates the PR, waits for CI, addresses review comments, auto-merges. Returns only after the PR is merged.

| | Description |
|---|---|
| **In** | Path to `/tmp/bug-explanation.md` (passed by ralph-fix-and-push) + fix applied to working tree |
| **Invokes** | `skills/create-pr.md` (passing bug explanation as PR description) → waits for CI → addresses comments → auto-merges |
| **Out** | `{ pr_url, merged: true }` — returned to ralph-fix-and-push |

#### `skills/create-pr.md`

**Job:** Read the bug explanation file and open a PR on GitHub using it as the PR description.

| | Description |
|---|---|
| **In** | Path to `/tmp/bug-explanation.md` + fix applied to working tree |
| **Out** | PR URL on GitHub |

---

### Generated scripts (contract summary)

| Script | Always? | Exits 0 when | Exits 1 when |
|---|---|---|---|
| `trigger.sh` | yes | flow successfully fired | could not invoke |
| `wait-for-completion.sh` | yes | flow reached success terminal state | flow reached failure terminal state or timed out |
| `fetch-logs.sh` | yes | logs fetched and printed to stdout | log source unreachable |
| `deploy.sh` | optional | fix deployed to environment | deploy failed |

---

## 3. Pseudocode / Technical Details

_Skipped — I/O contracts are sufficient for implementation._

---

## 4. Handoff to Related Plan Reconciliation

After all stages are approved, apply `.agent/skills/reconcile-plans/SKILL.md` to propagate contract updates across linked plans.
