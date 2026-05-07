---
name: flush-brain-data-before-cleanup
description: "Any script that deletes brain.json (including the Stop hook cleanup-session-files.sh) must flush derived persistent data — metrics, artifacts, etc. — from brain.json before the deletion, because brain.json is the only in-session source of that data."
user-invocable: false
---
## When to use

Whenever modifying or adding logic to any script that deletes `brain.json`, including:
- `cleanup-session-files.sh` (called by the Stop hook on session end or interruption)
- `dark-factory-agent` cleanup steps that delete brain.json before calling `cleanup-worktree.sh`

If brain.json contains data that must outlive the session (metrics, report fields, artifact paths), it must be flushed before deletion in every code path that removes brain.json.

## Steps

1. Identify all persistent data stored in brain.json that must survive session end. Common examples:
   - `metrics.*` fields accumulated by hook scripts (token counts, durations, phase counts)
   - `projectDir` — path to the permanent repo root (needed to write persistent files)
   - Any artifact paths that should be registered outside the worktree

2. In the cleanup script, read and flush that data **before** the `rm -f brain.json` call:
   ```bash
   BRAIN_PATH="$WORK_DIR/brain.json"

   if [ -f "$BRAIN_PATH" ]; then
     PROJECT_DIR=$(jq -r '.projectDir // empty' "$BRAIN_PATH" 2>/dev/null || true)
     if [ -n "$PROJECT_DIR" ] && [ -n "$CLAUDE_PLUGIN_ROOT" ]; then
       python3 "${CLAUDE_PLUGIN_ROOT}/scripts/update-metrics.py" \
         --csv "$PROJECT_DIR/metrics.csv" \
         --brain "$BRAIN_PATH" || true
     fi
   fi

   rm -f "$BRAIN_PATH"
   ```

3. Use `|| true` on flush calls so a failed flush never blocks the cleanup. Log the result to stderr for auditability:
   ```bash
   echo "cleanup-session-files | metrics-flushed | csv=$METRICS_CSV" >&2
   ```

4. Apply this same flush-before-delete pattern in every code path that removes brain.json: normal manufacture cleanup, error-path `cleanup()` trap functions, and the Stop hook script.

## Notes

- The Stop hook (`cleanup-session-files.sh`) fires on both normal session end and on interruption (user presses Ctrl+C, Claude Code crashes). If the flush only happens in the normal-path cleanup of `dark-factory-agent`, metrics are silently lost on interruption. Both paths need the flush.
- `CLAUDE_PLUGIN_ROOT` may be unset in some hook execution contexts. Always guard with `[ -n "$CLAUDE_PLUGIN_ROOT" ]` before referencing it, and provide a fallback or skip gracefully.
- This pattern complements `capture-project-dir-before-worktree`: that skill explains how to store `projectDir` in brain.json so the cleanup step can locate the permanent repo. This skill explains what to do with that path at deletion time.
- Do not attempt to write to `$WORK_DIR` after flushing, since the worktree may be deleted immediately after. Write only to `$PROJECT_DIR` paths derived from brain.json fields.
