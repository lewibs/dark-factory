---
name: converge-existing-resource-path
description: "When an agent detects that a long-lived resource (PR, branch, deployment) already exists, perform the side effects for that path (commit, push, record the existing URL) and fall through to the shared continuation — never early-return and skip the remaining steps."
user-invocable: false
---
## When to use

Any time an agent has a Step 0 / pre-check that detects an already-existing resource before attempting to create one. Common cases:

- A PR already exists on the current branch when pr-agent runs
- A deployment or release already exists when a deploy agent runs
- A remote branch already exists when a branch-create step runs

The wrong instinct is to early-return once the resource is found ("it already exists, nothing to do"). The correct pattern is to complete the side effects that belong to the "existing" path and then converge with the "new" path so that all downstream steps (CI watching, comment resolution, status reporting) still execute.

## Steps

1. At the top of the agent flow, check for the existing resource:
   ```
   existingResource = <lookup command> 2>/dev/null || null
   ```

2. If the resource exists, perform any side effects that are still needed (e.g., commit and push pending changes) and record the resource identifier:
   ```
   if existingResource is not null:
     git add --all
     git commit -m "<short description of pending changes>"
     git push
     resource_url = existingResource
   # (if resource does not exist, resource_url will be set in the creation step below)
   ```

3. Gate the creation step on the resource not yet existing — do NOT return early:
   ```
   if existingResource is null:
     resource_url = <create resource>
   ```

4. Continue with all downstream steps unconditionally using `resource_url`:
   ```
   write brain-patch.json: { "resourceUrl": resource_url }
   # watch CI, resolve comments, etc.
   ```

## Notes

- The bug this pattern prevents: early-returning after detecting the existing resource causes all downstream steps (CI watching, comment resolution, merging) to be skipped. The PR sits open and unmonitored forever.
- Both branches (existing and new) must set `resource_url` before the downstream steps; downstream steps are always unconditional.
- If the pending commit in Step 2 produces nothing to commit (working tree clean), the `git commit` will fail with "nothing to commit" — guard with `git status --porcelain` before committing, or use `git commit --allow-empty` only if an explicit marker commit is desired.
- This pattern was introduced in the 2026-05-04 fix to `agents/pr/agents/pr-agent.md` to fix pr-agent skipping CI watching when an existing PR was detected.
