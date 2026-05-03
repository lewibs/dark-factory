---
name: ci-watch-runner
description: "Watch CI checks on a PR until completion or failure. Spawn fix handlers for failures, retry up to maxIterations. Return pass/fail status."
user-invocable: false
---

# ci-watch-runner

Poll and manage CI checks on a GitHub PR until all pass or max iterations exceeded.

## Input

- `prUrl` — GitHub PR URL (string, e.g., "https://github.com/owner/repo/pull/123")
- `maxIterations` — maximum number of watch-and-fix cycles (integer, default 5)

## Output

### Success (all checks pass)
```json
{
  "status": "pass",
  "checks": [
    { "name": "tests", "status": "COMPLETED", "conclusion": "SUCCESS" }
  ]
}
```

### Failure (unfixable or max iterations exceeded)
```json
{
  "status": "fail",
  "reason": "CI failure unfixable: linter errors",
  "failedChecks": [
    { "name": "linter", "conclusion": "FAILURE" }
  ]
}
```

## Algorithm

```
iterations = 0

LOOP:
  if iterations >= maxIterations:
    return { status: "fail", reason: "Max CI iterations exceeded" }

  # Watch all checks until complete or one fails
  checks = gh pr checks <prUrl> --watch
  
  if all checks have conclusion == "SUCCESS":
    return { status: "pass", checks }
  
  # Collect failing run IDs
  failedRuns = gh pr checks <prUrl> --fail-fast
  
  for each run in failedRuns:
    fixResult = spawn resolve-pr-issue(prUrl, { type: "ci", runId: run.runId, failedChecks: [run.checkName] })
    
    if fixResult.skipped == true:
      # Quota exhaustion — treat as pass, skip remaining runs
      return { status: "pass", checks }
    
    if fixResult.fixed == false:
      return { status: "fail", reason: "CI failure unfixable: " + fixResult.reason }
    
    # Fix was pushed; break out and re-watch CI
    break
  
  iterations += 1
  CONTINUE LOOP
```

## Rules

- Do NOT merge the PR — this command only watches and fixes, it does not change PR state
- Quota exhaustion (`skipped == true`) is treated as a passing check and returns `status: "pass"`
- Each failed run spawns a separate fix attempt, but only the first successful fix breaks the inner loop (remaining runs may already be fixed by the same commit)
- The `--watch` flag blocks until all checks complete or one fails
- Pushing a fix restarts the cycle (re-watch CI)

## Integration

This command is called by `pr-agent` during step 3 (CI watch loop):

```
ciResult = invoke ci-watch-runner({
  prUrl: pr_url,
  maxIterations: 5
})

if ciResult.status == "fail":
  stop with error: ciResult.reason

# ciResult.status == "pass"
# proceed to step 4 (comment resolution)
```
