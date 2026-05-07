---
name: metrics
description: "Display ranked list of slowest and most token-intensive agents and skills from metrics.csv"
---

# metrics

Display a ranked list of agents and skills by execution time and token usage.

## Output

Displays two ranked tables:
1. **Slowest Agents/Skills** — sorted by avg_runtime (milliseconds) in descending order
2. **Highest Token Usage** — sorted by avg_tokens in descending order

Each table shows:
- Agent/Skill name
- Average runtime (ms)
- Average tokens
- Number of runs
- Total runtime (ms)
- Total tokens

## Algorithm

1. Read metrics.csv from the project root
2. Parse CSV rows (skip header and rows with 0.0 values for both metrics)
3. Sort by avg_runtime descending → display top slowest
4. Sort by avg_tokens descending → display top token-heaviest
5. Format as human-readable tables

## Implementation

The command is implemented as a simple Python script that:
- Reads the CSV file
- Filters out entries with zero metrics
- Generates two sorted rankings
- Formats output as readable tables
