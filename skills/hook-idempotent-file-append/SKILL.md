---
name: hook-idempotent-file-append
description: "When a PostToolUse or end-of-agent hook appends content to a file, guard with grep to prevent duplicate appends across multiple hook invocations."
user-invocable: false
---
## When to use

Any time you write a bash hook script that appends a line or block of text to a file (PR body, log file, summary file, etc.) and the hook may be invoked more than once per agent session. PostToolUse hooks in particular are invoked after every matching tool call, so they will run multiple times.

## Steps

1. Before appending, grep the target file for a unique string that will appear in the appended content:

   ```bash
   if grep -q "unique sentinel string" "$TARGET_FILE"; then
       echo "Content already present, skipping" >&2
       exit 0
   fi
   ```

2. Choose a sentinel string that is specific enough to not appear by accident but present in every valid append (e.g., a URL, a distinctive phrase, or a marker comment).

3. Perform the append only when the sentinel is absent:

   ```bash
   {
       cat "$TARGET_FILE"
       echo ""
       echo "--- appended content ---"
   } > "$TARGET_FILE.tmp"
   mv "$TARGET_FILE.tmp" "$TARGET_FILE"
   ```

   Use a `.tmp` file + `mv` to make the write atomic.

4. If the file does not exist yet, exit 0 gracefully — the hook may be firing before the file is created:

   ```bash
   if [[ ! -f "$TARGET_FILE" ]]; then
       exit 0
   fi
   ```

## Notes

- Always write to a `.tmp` file and then `mv` — never append with `>>` when ordering matters, because `>>` cannot include the existing content atomically.
- The grep sentinel must match a substring that appears in the appended block. Avoid matching something in the original file body that could produce false positives.
- Log skips to stderr (`>&2`) so the hook's stdout is not polluted; Yama/Claude Code reads hook stdout.
- This pattern applies equally to SubagentStop hooks that could be fired on retry paths.
