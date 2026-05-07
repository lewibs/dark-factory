# Plan: Add /metrics Command

## System Intent

Create a new `/dark-factory:metrics` plugin command that displays a ranked list of agents and skills by slowest average runtime and highest token usage.

The command reads from `metrics.csv` in the project root and displays two ranked tables:
1. Slowest agents/skills by avg_runtime (descending)
2. Most token-intensive agents/skills by avg_tokens (descending)

Each ranking shows the top 15 entries with columns for:
- Agent/Skill name
- Average runtime (ms)
- Average tokens
- Number of runs
- Total runtime
- Total tokens

## Implementation

### Files Created

- `commands/metrics.md` — Plugin command definition and documentation
- `commands/metrics/metrics.py` — Python script implementing the ranking and display logic

### Key Features

- Reads metrics.csv using Python's csv module
- Filters out entries where both avg_runtime and avg_tokens are 0.0
- Sorts by runtime and tokens separately
- Formats output as readable ASCII tables
- Handles missing files gracefully with error messages
- Searches multiple common locations for metrics.csv

### Testing

The implementation has been tested against the actual metrics.csv file and displays:
- Top slowest agents: debugger-agent (418.5s), update-documentation-agent (172.2s), code-review-orchestrator-agent (158.9s)
- Top token users: Explore (1786.0 avg), planning-agent (1155.0 avg), investigation-agent (1081.0 avg)

## Approval Gates

- [x] Draft plan complete
- [x] Implementation complete and tested
- [x] All files committed to feature branch

## Completion Status

Ready for code review and PR.
