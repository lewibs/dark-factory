# Metrics CSV Tracking

## Plan Metadata

- Plan type: `plan`
- Parent plan: N/A
- Depends on: N/A
- Status: `draft`

Status semantics:
- `draft`: Plan is being created or updated and is not final.
- `approved`: Plan is approved but not yet applied in code.
- `documentation`: Code currently exists and matches the plan contract.

## System Intent

- What is being built: A persistent, append-and-aggregate CSV file that records AI agent/skill performance metrics (runtime, token usage, run count). Hooks accumulate metrics into brain.json during a manufacture run; at the end of manufacture the dark-factory-agent calls a Python script once to flush brain.json metrics into the permanent CSV.
- Primary consumer(s): Developers reviewing system performance over time.
- Boundary (black-box scope only): Hooks are pure bash — no agent calls, no Claude API. PreToolUse captures start time and agent/skill name into brain.json. PostToolUse computes elapsed time and token counts and accumulates them into brain.json. The CSV write happens exactly once per manufacture run, in the orchestrator cleanup step.

## Stage Gate Tracker

- [x] Stage 1 Mermaid approved
- [x] Stage 2 Flows approved

## Mermaid Diagram

```mermaid
graph TD
  PreHook["PreToolUse Hook\n(pre-tool-use-hook.sh)"]:::modified
  PostHook["PostToolUse Hook\n(post-tool-use-hook.sh)"]:::modified
  Brain["brain.json\nmetrics accumulator"]:::modified
  Orchestrator["dark-factory-agent\ncleanup step"]:::modified
  MetricsScript["scripts/update-metrics.py\n(new)"]:::created
  CSV["$PROJECT_DIR/metrics.csv\n(permanent)"]:::created

  PreHook -->|"write start_ms + agent/skill name"| Brain
  PostHook -->|"accumulate elapsed_ms + tokens\nper agent/skill key"| Brain
  Orchestrator -->|"pass brain.json path"| MetricsScript
  Brain -->|"metrics section"| MetricsScript
  MetricsScript -->|"upsert rows, recompute averages"| CSV

classDef unchanged fill:#d3d3d3,stroke:#666,stroke-width:1px;
classDef modified fill:#ffe0a3,stroke:#666,stroke-width:1px;
classDef created fill:#a8e6a3,stroke:#666,stroke-width:1px;
```

## Flows

### Global Types

```txt
StandardError {
  message: string (human-readable description of what went wrong)
}

MetricsRow {
  agent:        string  (agent name — from hook payload or env)
  skill:        string  (skill or tool name — from hook payload)
  avg_runtime:  float   (milliseconds — computed: sum_runtime / runs)
  avg_tokens:   float   (tokens — computed: sum_tokens / runs)
  runs:         int     (total invocation count)
}

InternalAccumulatorRow {
  agent:        string
  skill:        string
  sum_runtime:  float   (running total of runtime_ms values)
  sum_tokens:   float   (running total of token counts)
  runs:         int
}
```

### Flow: `preHookCapturesStart`

Fires on every PreToolUse event for `Agent` or `Skill` tool calls.

- Test files: `tests/test_hooks.py`
- Core files: `agents/dark-factory/scripts/pre-tool-use-hook.sh`

#### Paths

| path | input | output | path-type | notes | updated |
|---|---|---|---|---|---|
| `preHookCapturesStart.agent-tool` | tool_name = "Agent" | brain.json metrics[key].start_ms written | happy path | key = agent name extracted from subagent_type or prompt | |
| `preHookCapturesStart.skill-tool` | tool_name = "Skill" | brain.json metrics[key].start_ms written | happy path | key = skill field from tool input | |
| `preHookCapturesStart.other-tool` | tool_name = anything else | no-op | happy path | hook exits 0 immediately | |
| `preHookCapturesStart.no-brain` | DARK_FACTORY_WORK_DIR unset or brain.json missing | no-op, log to stderr | happy path | metrics disabled gracefully | |

#### Pseudocode

```
# pre-tool-use-hook.sh addition:
HOOK_INPUT = read stdin
TOOL_NAME  = jq '.tool_name' <<< HOOK_INPUT

if TOOL_NAME not in ["Agent", "Skill"]: exit 0
if DARK_FACTORY_WORK_DIR unset or brain.json missing: exit 0

if TOOL_NAME == "Agent":
  KEY = jq '.tool_input.subagent_type // "unknown"' <<< HOOK_INPUT
  # fallback: grep agents/*.md path from prompt, take basename without .md
if TOOL_NAME == "Skill":
  KEY = jq '.tool_input.skill // "unknown"' <<< HOOK_INPUT

NOW_MS = $(date +%s%3N)

# write into brain.json metrics section using jq
jq --arg key "$KEY" --argjson now $NOW_MS \
  '.metrics[$key].start_ms = $now' brain.json > brain.tmp && mv brain.tmp brain.json
```

---

### Flow: `postHookAccumulatesMetrics`

Fires on every PostToolUse event for `Agent` or `Skill` tool calls.

- Test files: `tests/test_hooks.py`
- Core files: `agents/dark-factory/scripts/post-tool-use-hook.sh`

#### Paths

| path | input | output | path-type | notes | updated |
|---|---|---|---|---|---|
| `postHookAccumulatesMetrics.success` | tool completed, brain.json has start_ms for key | brain.json metrics[key] updated: elapsed_ms += delta, tokens += n, runs += 1 | happy path | | |
| `postHookAccumulatesMetrics.missing-start` | start_ms absent for key | elapsed_ms = 0, still accumulates tokens + runs | happy path | Handles out-of-order or first-run edge case | |
| `postHookAccumulatesMetrics.no-usage` | tool_response has no usage field | tokens defaults to 0 | happy path | | |
| `postHookAccumulatesMetrics.other-tool` | tool_name not Agent or Skill | no-op | happy path | | |

#### Pseudocode

```
# post-tool-use-hook.sh addition (after existing brain merge):
HOOK_INPUT = read stdin (already consumed — use saved copy or re-read from env)
TOOL_NAME  = jq '.tool_name' <<< HOOK_INPUT

if TOOL_NAME not in ["Agent", "Skill"]: exit 0
if DARK_FACTORY_WORK_DIR unset or brain.json missing: exit 0

# same key extraction as pre-hook
KEY = extract_key(HOOK_INPUT, TOOL_NAME)

NOW_MS    = $(date +%s%3N)
START_MS  = jq --arg k "$KEY" '.metrics[$k].start_ms // 0' brain.json
ELAPSED   = $((NOW_MS - START_MS))

TOKENS = jq '(.tool_response.usage.input_tokens // 0) + (.tool_response.usage.output_tokens // 0)' <<< HOOK_INPUT

jq --arg key "$KEY" --argjson elapsed $ELAPSED --argjson tokens $TOKENS '
  .metrics[$key].elapsed_ms = ((.metrics[$key].elapsed_ms // 0) + $elapsed) |
  .metrics[$key].tokens     = ((.metrics[$key].tokens     // 0) + $tokens)  |
  .metrics[$key].runs       = ((.metrics[$key].runs       // 0) + 1)        |
  del(.metrics[$key].start_ms)
' brain.json > brain.tmp && mv brain.tmp brain.json
```

---

### Flow: `orchestratorFlushesCSV`

Fires once at the end of manufacture, in dark-factory-agent before cleanup-worktree.sh.

- Test files: `tests/test_update_metrics.py`
- Core files: `scripts/update-metrics.py`, `agents/dark-factory/agents/dark-factory-agent.md`

#### Types

```txt
UpdateMetricsInput {
  csv_path:   string  (absolute path — read from brain.json.workDir + "/metrics.csv")
  brain_path: string  (absolute path to brain.json)
}

UpdateMetricsOutput {
  rows_written: int
}
```

#### Paths

| path | input | output | path-type | notes | updated |
|---|---|---|---|---|---|
| `orchestratorFlushesCSV.success` | brain.json has metrics section | CSV upserted, averages recomputed | happy path | | |
| `orchestratorFlushesCSV.no-metrics` | brain.json has no metrics key | no-op, CSV unchanged | happy path | Repair route never touches brain.json | |
| `orchestratorFlushesCSV.csv-new` | csv_path does not exist | CSV created with headers + rows | happy path | | |
| `orchestratorFlushesCSV.script-error` | any | error logged to stderr, manufacture continues | error | Non-fatal — metrics failure never blocks a PR | |

#### Pseudocode

```
# dark-factory-agent — before rm -f brain.json:
PROJECT_DIR = jq '.workDir' brain.json
METRICS_CSV = "$PROJECT_DIR/metrics.csv"
python3 scripts/update-metrics.py --csv "$METRICS_CSV" --brain "$WORK_DIR/brain.json" || true

# scripts/update-metrics.py:
def main(csv_path, brain_path):
  brain = json.load(brain_path)
  metrics = brain.get("metrics", {})
  if not metrics: return

  rows = read_csv(csv_path)   # [] if file absent
  for key, data in metrics.items():
    agent, _, skill = key.partition("/")   # key format: "agent/skill" or just "agent"
    elapsed = data.get("elapsed_ms", 0)
    tokens  = data.get("tokens", 0)
    runs    = data.get("runs", 1)
    upsert(rows, agent, skill, elapsed, tokens, runs)

  write_csv(csv_path, rows)   # recomputes avg_runtime, avg_tokens from sums

def upsert(rows, agent, skill, elapsed_ms, tokens, runs):
  existing = find(rows, agent, skill)
  if existing:
    existing["sum_runtime"] += elapsed_ms
    existing["sum_tokens"]  += tokens
    existing["runs"]        += runs
  else:
    rows.append({"agent": agent, "skill": skill,
                 "sum_runtime": elapsed_ms, "sum_tokens": tokens, "runs": runs})
  for row in rows:
    row["avg_runtime"] = row["sum_runtime"] / row["runs"]
    row["avg_tokens"]  = row["sum_tokens"]  / row["runs"]
```

#### CSV file format

```
agent,skill,avg_runtime,avg_tokens,runs,sum_runtime,sum_tokens
feature-agent,planning-agent,4523.1,12400.0,3,13569.3,37200.0
```

`sum_runtime` and `sum_tokens` are stored so averages stay correct across multiple runs without raw history.

### Flow: `csvInitialization`

- Test files: `tests/test_update_metrics.py`
- Core files: `scripts/update-metrics.py`

#### Paths

| path | input | output | path-type | notes | updated |
|---|---|---|---|---|---|
| `csvInitialization.new-file` | csv_path does not exist | CSV created with header row | happy path | Script creates parent dirs if needed | |
| `csvInitialization.existing-file` | csv_path exists | CSV read and updated | happy path | | |

## Implementation Checklist

The following files must be created or modified:

1. **`scripts/update-metrics.py`** (new) — Python script. CLI args: `--csv <path>`, `--brain <path>`. Reads brain.json metrics section, upserts rows in CSV, recomputes averages. Non-fatal: exits 0 on any error after logging to stderr.

2. **`agents/dark-factory/scripts/pre-tool-use-hook.sh`** (modify) — For Agent/Skill tool calls only: extract key (agent name or skill name), write `start_ms` into `brain.json.metrics[key]` via jq. No-op if brain.json absent. All logging to stderr.

3. **`agents/dark-factory/scripts/post-tool-use-hook.sh`** (modify) — For Agent/Skill tool calls only: compute `elapsed_ms = now - start_ms`, extract tokens from `tool_response.usage`, accumulate into `brain.json.metrics[key]`. Delete `start_ms`. All logging to stderr.

4. **`agents/dark-factory/agents/dark-factory-agent.md`** (modify) — Add step before `rm -f brain.json`: call `python3 scripts/update-metrics.py --csv "$PROJECT_DIR/metrics.csv" --brain "$WORK_DIR/brain.json" || true`.

5. **`tests/test_update_metrics.py`** (new) — Pytest unit tests covering: new CSV created with headers, row upsert increments runs, averages recomputed correctly, no-metrics key is a no-op, missing usage fields default to 0.

6. **`tests/test_hooks.py`** (new) — Pytest tests using subprocess per `dark-factory:test-bash-hook-scripts-with-pytest` skill: PreToolUse writes start_ms to brain.json, PostToolUse accumulates elapsed+tokens+runs, non-Agent/Skill tools are ignored, missing brain.json is a no-op.

7. **`metrics.csv`** — Not created by implementation; created on first manufacture completion. Permanent file at `$PROJECT_DIR/metrics.csv`. Do not gitignore.

## Logs

| Source | Location |
|--------|----------|
| pre-tool-use-hook.sh metrics writes | stderr — `pre-tool-use-hook \| metrics-capture \| key=feature-agent start_ms=1234567890` |
| post-tool-use-hook.sh metrics writes | stderr — `post-tool-use-hook \| metrics-accumulate \| key=feature-agent elapsed_ms=4523 tokens=12400 runs=1` |
| update-metrics.py flush | stderr — `update-metrics \| flush \| rows=3 csv=/path/metrics.csv` |
| update-metrics.py errors | stderr — non-fatal, manufacture continues |

## Deployment

- Mechanism: `local only` — scripts are bash/python, no build step required.
- Deploy command: N/A (hooks are always-on via `.claude/settings.json`)
- Notes: `metrics.csv` persists at `$PROJECT_DIR/metrics.csv` across sessions. Do not `.gitignore` it — it is the permanent running total.
