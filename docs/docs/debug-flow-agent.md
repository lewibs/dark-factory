# debug-flow-agent

**Role**: Runs an integration flow, waits for it to finish, fetches logs, and coordinates the entire fix — from diagnosis through PR submission.

**Model**: Sonnet.

**User-Invocable**: No (invoked by ralph-fix-and-push).

## Overview

The debug-flow-agent triggers a named integration flow, waits for its terminal state, and — if it fails — hands off to debugger-agent for systematic diagnosis and fix implementation. Once the fix is verified (tests pass), debug-flow-agent commits the changes and invokes pr-agent to submit a PR. It returns a PR URL on success.

The agent does NOT stop at diagnosis. It must drive the flow to a verified fix and open a PR.

## Input

- Paths to three scripts (passed by ralph-fix-and-push):
  - `trigger.sh` — fires the integration flow
  - `wait-for-completion.sh` — blocks until flow reaches a terminal state
  - `fetch-logs.sh` — retrieves logs from the last run

## Workflow (8 Steps)

### Step 1: Trigger the Flow

Runs `bash trigger.sh` to fire the integration flow.

### Step 2: Wait for Completion

Runs `bash wait-for-completion.sh` and checks the exit code:
- Exit code 0 → flow succeeded. Returns `exit_code=0` immediately. Does NOT fetch logs or debug.
- Exit code 1 → flow failed. Continues to Step 3.

**Rule**: Never read logs from a run that has not finished. Always wait before fetching logs.

### Step 3: Fetch Logs

Runs `bash fetch-logs.sh` to retrieve logs from the failed run.

### Step 4: Invoke debugger-agent

Invokes `debugger-agent` with the fetched logs as context. debugger-agent performs systematic debugging and implements the fix by applying code changes to the working tree. debugger-agent does NOT commit — committing is debug-flow-agent's responsibility.

### Step 5: Verify the Fix (up to 3 Iterations)

After debugger-agent returns, verifies the fix was implemented:

1. Runs `git diff --exit-code` to confirm code changes exist in the working tree. If no changes exist, the fix was not applied — reports back to debugger-agent for another iteration.
2. Runs the full test suite (`npm test` or `pytest`) to confirm tests pass. If tests fail, reports back to debugger-agent with the failure output for another iteration.

If after 3 total iterations the fix is still not working, returns `exit_code=1` with the bug explanation and last test failure output.

### Step 6: Commit the Fix

Once the fix is verified (tests pass and changes are in the working tree):

```bash
git add --all && git commit -m "fix: <title from bug explanation>"
```

### Step 7: Invoke pr-agent

Invokes `pr-agent` with:
- `taskDescription` — the bug explanation from the bug audit log written by debugger-agent
- `bugFilePath` — the absolute path to the bug audit log file

pr-agent writes the PR to GitHub and returns the PR URL.

### Step 8: Return Result

Returns the PR URL and `exit_code=0` to indicate success, or `exit_code=1` with bug explanation if the fix could not be implemented.

## Key Design Rules

1. **Do not stop at diagnosis** — the full cycle must reach PR submission
2. **Never skip the wait step** — always run wait-for-completion.sh before reading logs, even if trigger.sh appears to have finished
3. **Do not run deploy.sh** — PR creation is handled via pr-agent
4. **Committing is this agent's responsibility** — debugger-agent applies changes but does not commit
5. **Retry up to 3 total iterations** — if the fix is not working after 3 attempts, return failure with diagnostic information
6. **Never use Explore subagent_type directly** — always route codebase research through `investigation-agent`

## Dependencies

- **Sub-agents**: debugger-agent, pr-agent
- **Scripts**: trigger.sh, wait-for-completion.sh, fetch-logs.sh (passed in by ralph-fix-and-push)

## Tools

- Read, Write, Edit, Bash, Grep, Glob, Agent
- Allowed Bash commands: `bash trigger.sh`, `bash wait-for-completion.sh`, `bash fetch-logs.sh`, `git *`

## Return Value

On success:
```json
{
  "exit_code": 0,
  "prUrl": "<github PR URL>"
}
```

On failure:
```json
{
  "exit_code": 1,
  "bugExplanation": "<summary of bug and why fix could not be applied>",
  "lastTestFailure": "<test output from last attempt>"
}
```

On flow already passing:
```json
{
  "exit_code": 0
}
```

## Error Handling

- If flow succeeded on trigger: returns `exit_code=0` immediately without debugging
- If debugger-agent does not apply changes after 3 iterations: returns `exit_code=1` with diagnostic info
- If tests fail after 3 iterations: returns `exit_code=1` with last test output
- If pr-agent fails: returns `exit_code=1` noting PR was not created
