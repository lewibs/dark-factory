---
name: flock-shared-file-in-hooks
description: "How to safely write a shared JSON file (e.g. brain.json) from Claude Code pre/post hooks that may fire concurrently for nested agent calls, using flock inside a subshell."
user-invocable: false
---
## When to use

Whenever a pre-tool-use or post-tool-use hook script writes to a file that might also be written by another hook instance running concurrently — for example, when nested `Agent` or `Skill` tool calls trigger the same hook at multiple depths simultaneously.

Without locking, the mktemp+mv write pattern is not atomic across multiple processes: two hooks can both read the same base file, produce two separate tmp files, and the last `mv` silently discards the first writer's changes.

## Steps

1. Declare a lock file path alongside the shared file:
   ```bash
   BRAIN_PATH="${DARK_FACTORY_WORK_DIR}/brain.json"
   BRAIN_LOCK="${BRAIN_PATH}.lock"
   ```

2. Wrap every critical section (read-modify-write of the shared file) in a subshell that holds an exclusive flock on fd 200:
   ```bash
   (
     flock -x 200
     TMP=$(mktemp /tmp/brain-XXXXXX.json)
     jq '<your transform>' "$BRAIN_PATH" > "$TMP" && mv "$TMP" "$BRAIN_PATH"
   ) 200>"$BRAIN_LOCK"
   ```

3. Apply this pattern to every place in the same script that writes the shared file — if a script has three separate write blocks, each must be wrapped independently. Do not hold the lock across unrelated work.

4. The `.lock` file is created automatically by the shell redirect and does not need to be pre-created or cleaned up. It persists harmlessly between runs.

## Notes

- `flock -x 200` blocks until the lock is acquired. If a hook hangs (e.g., jq crashes), the lock is released automatically when the subshell exits.
- The lock file itself contains no data — only the file descriptor matters.
- Using fd 200 is a convention; any unused fd number works, but 200 is safely above normal stdio/stderr.
- This pattern is safe even when the hook fires at only one depth; the subshell overhead is negligible for file operations.
- Do NOT lock across a `jq` read that happens outside the subshell and then a write inside — re-read the file inside the locked section if the value is needed for the mutation.
