---
name: sequential-phase-gating-brain-json
description: "How to enforce strict sequential phase ordering for an agent by storing completed phase numbers in brain.json and gating advancement in a PreToolUse hook."
user-invocable: false
---
## When to use

When an agent has a strictly-ordered numbered workflow (phase 1 → 2 → 3 … N) and you want to prevent phases from being skipped or executed out of order. This pattern uses `brain.json` as the shared state store and a `PreToolUse` hook as the enforcement gate.

This is distinct from the boolean `*-running` / `*-complete` phase flags (see `brain-hook-driven-state`): those flags track which phase is currently active; this pattern tracks a cumulative list of completed phase numbers so that any attempt to jump ahead is blocked until all prerequisites are satisfied.

## Steps

1. Add a `phases.completedPhases` array to `brain.json` at initialization time (set to `[]`):
   ```json
   {
     "phases": {
       "completedPhases": []
     }
   }
   ```
   This key is separate from the existing `*-running` / `*-complete` boolean fields. Both can coexist.

2. Define an agent allowlist in the enforcement hook script as a bash associative array mapping agent name → total phase count (informational; only the array contents are used for gating):
   ```bash
   declare -A PHASE_MAP
   PHASE_MAP["dark-factory-agent"]=7
   PHASE_MAP["update-documentation-agent"]=3
   ```
   Agents not in the map pass through unconditionally.

3. In the `checkPhaseOrder` function:
   - Allow phase 1 unconditionally (no prerequisites).
   - If `brain.json` does not exist, allow (fail-open; safe for non-dark-factory sessions).
   - Read `completedPhases` with: `jq -r '.phases.completedPhases // [] | @json' brain.json`
   - Iterate phases `1 … currentPhase-1`; for each, check membership with jq: `map(select(. == $p)) | length > 0`
   - If any prerequisite is absent, output `{"allowed":false,"reason":"..."}` and exit 0.
   - Output `{"allowed":true}` and exit 0 on success.

4. In the `markPhaseComplete` function (called at the end of each phase):
   - Use `flock` around the read-modify-write (see `flock-shared-file-in-hooks` skill).
   - Merge the new phase number with deduplication and sort: `.phases.completedPhases = ((.phases.completedPhases // []) + [$p] | unique | sort)`
   - Verify the write succeeded by re-reading and checking membership before returning `{"updated":true}`.
   - Return `{"updated":false,"error":"..."}` on any write failure; do not exit non-zero (hooks must exit 0 to avoid crashing Claude Code).

5. Register the enforcement hook as `PreToolUse` (and optionally `PreAgentUse`) in `hooks/hooks.json`:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "",
           "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/phase-order-enforcement-hook.sh\"" }]
         }
       ]
     }
   }
   ```
   An empty `matcher` fires the hook for every tool call. The hook exits early (no-op) for agents not in the `PHASE_MAP`.

## Notes

- The hook must always exit 0. A non-zero exit causes Claude Code to treat the hook as crashed, not as a blocked tool call. Returning `{"allowed":false}` in JSON is the correct way to block.
- Fail-open (allow) when `brain.json` is absent. This makes the hook safe for Claude Code sessions that are not running under the dark-factory orchestrator.
- The `completedPhases` array must only be written by the `mark-phase-complete` command path, not by the agent directly. Agents write `brain-patch.json`; the post-hook merges it. Phase completion is a side-channel to the normal patch flow and is written by the hook itself.
- When adding a new phase-ordered agent, add it to `PHASE_MAP` in the enforcement hook and also to the `PHASE_AGENTS` allowlist in `pre-tool-use-hook.sh` / `post-tool-use-hook.sh` (see `phase-agent-allowlist` skill) so the boolean running/complete flags also fire for it.
- The `phases.completedPhases` array coexists with the boolean `*-running`/`*-complete` fields — they serve complementary roles. The boolean fields track "what is currently running"; the integer array tracks "what has definitively finished."
