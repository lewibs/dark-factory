---
name: comment-resolution-runner
description: "Watch for and resolve review comments on a PR. Handle each unresolved thread, re-run CI after resolving, retry up to maxIterations. Return resolved/failed status."
user-invocable: false
---

# comment-resolution-runner

Iterate through unresolved review threads on a PR, address each one, re-check CI, and return when all threads are resolved.

## Input

- `prUrl` — GitHub PR URL (string, e.g., "https://github.com/owner/repo/pull/123")
- `prNodeId` — PR GraphQL node ID (string, from `gh api graphql`)
- `maxIterations` — maximum number of resolution cycles (integer, default 5)

## Output

### Success (all threads resolved)
```json
{
  "status": "all-resolved",
  "threadsResolved": 3
}
```

### Failure (unfixable thread or max iterations)
```json
{
  "status": "failed",
  "reason": "Review thread unfixable: reviewer requires design doc",
  "threadId": "PR_kwDOT2Q_2M123456789"
}
```

## Algorithm

```
iterations = 0

LOOP:
  if iterations >= maxIterations:
    return { status: "failed", reason: "Comment resolution loop exceeded MAX_COMMENT_ITERATIONS" }

  # Fetch all unresolved review threads
  unresolvedThreads = gh api graphql list-review-threads(prNodeId)
    // filter to isResolved == false

  if unresolvedThreads is empty:
    return { status: "all-resolved", threadsResolved: iterations }

  for each thread in unresolvedThreads:
    fixResult = spawn resolve-pr-issue(prUrl, { type: "review", threadId: thread.threadId, comments: thread.comments })

    if fixResult.fixed == false:
      return { status: "failed", reason: "Review thread unfixable: " + fixResult.reason, threadId: thread.threadId }

    # fixResult.fixed == true — fix was pushed and thread resolved via GraphQL

  # After resolving all threads in this round, re-check CI before checking for more threads
  ciResult = ci-watch-runner(prUrl, maxIterations=5)
  
  if ciResult.status == "fail":
    return { status: "failed", reason: "CI failed after resolving threads: " + ciResult.reason }

  iterations += 1
  CONTINUE LOOP  // check for any newly added threads
```

## Rules

- Threads are queried via GraphQL using `prNodeId` (not PR number)
- Each resolved thread must be marked as resolved via GraphQL mutation before proceeding
- After resolving all threads in a round, re-run CI via `ci-watch-runner` before checking for newly added threads
- Quota exhaustion during CI re-check is treated as a passing check (threads stay resolved)
- If a new thread is added after the previous round, the loop continues
- Each thread spawns a separate fix attempt via `resolve-pr-issue`

## Integration

This command is called by `pr-agent` during step 4 (comment resolution loop):

```
# Get PR node ID first
prNodeId = gh api graphql -f query='query($owner:String!,$repo:String!,$number:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$number){id}}}' ...

commentResult = invoke comment-resolution-runner({
  prUrl: pr_url,
  prNodeId: prNodeId,
  maxIterations: 5
})

if commentResult.status == "failed":
  stop with error: commentResult.reason

# commentResult.status == "all-resolved"
# proceed to step 5 (return ready status)
```
