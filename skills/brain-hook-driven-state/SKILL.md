---
name: brain-hook-driven-state
description: "How to wire cross-agent shared state through Claude Code PreToolUse/PostToolUse hooks: the orchestrator creates brain.json, hooks inject it into sub-agent prompts and merge sub-agent patches back, and sub-agents only write brain-patch.json."
user-invocable: false
---
## When to use

When adding a new sub-agent to the dark-factory pipeline, or when modifying how shared state (brain.json) is created, injected, or consumed. Use this instead of passing brainPath as an explicit argument to each sub-agent.

## Steps

### Orchestrator (dark-factory-agent)

1. After `prep-feature-dir.sh` captures `WORK_DIR`, write `$WORK_DIR/brain.json` with all fields initialized. The `phases` object must have every phase pair (`*-running` / `*-complete`) set to `false`, except `prep-complete: true`.

2. Export the env var so hook scripts (child processes) can find brain.json:
   ```bash
   export DARK_FACTORY_WORK_DIR=<WORK_DIR>
   ```
   The variable must be `export`-ed — not merely set — because hooks run as separate processes.

3. Invoke sub-agents normally. Do NOT pass brainPath as an argument; the pre-hook injects brain state automatically.

4. After each sub-agent returns, read `$WORK_DIR/brain.json` to get its output values (e.g., `planFilePath`, `prUrl`). The post-hook has already merged the sub-agent's brain-patch.json into brain.json by the time the Agent tool call returns.

5. Before calling `cleanup-worktree.sh`, delete brain.json:
   ```bash
   rm -f $WORK_DIR/brain.json
   ```
   This is mandatory — the cleanup script removes the entire worktree directory.

### Pre-hook (`pre-tool-use-hook.sh`)

- Triggered on every `Agent` tool call (set `"matcher": "Agent"` in settings.json).
- Reads brain.json from `$DARK_FACTORY_WORK_DIR/brain.json`.
- Finds the first phase that is not yet started (no `-running` suffix, no `-complete` suffix, value `false`) and sets `*-running = true`.
- Prepends the brain JSON as read-only context to the sub-agent's prompt.
- Emits the modified tool input JSON on stdout (see `claude-code-hook-stdout-reserved` skill).
- If brain.json does not exist, passes through unchanged and exits 0 — this makes the hook safe for non-dark-factory Claude sessions.

### Post-hook (`post-tool-use-hook.sh`)

- Triggered after every `Agent` tool call returns.
- Merges `$DARK_FACTORY_WORK_DIR/brain-patch.json` into brain.json using `jq -s '.[0] * .[1]'`, then deletes the patch file.
- Finds the currently-running phase (the one with `*-running = true`) and flips it to `*-running = false` / `*-complete = true`.
- If brain.json does not exist, exits 0 silently.

### Sub-agents

- Do NOT read brain.json directly — brain state is already injected into the prompt by the pre-hook.
- Do NOT write brain.json directly.
- After producing output, write ONLY your specific output fields to `$DARK_FACTORY_WORK_DIR/brain-patch.json`:
  ```json
  { "planFilePath": "/absolute/path/to/plan.md" }
  ```
- If `DARK_FACTORY_WORK_DIR` is not set or the sub-agent has no output to record, skip writing the patch entirely.
- The patch file is deleted by the post-hook after it is merged; sub-agents must not re-read it.

### Registering hooks in settings.json

```json
"hooks": {
  "PreToolUse": [
    { "matcher": "Agent", "hooks": [{ "type": "command", "command": "bash agents/dark-factory/scripts/pre-tool-use-hook.sh" }] }
  ],
  "PostToolUse": [
    { "matcher": "Agent", "hooks": [{ "type": "command", "command": "bash agents/dark-factory/scripts/post-tool-use-hook.sh" }] }
  ]
}
```

## Notes

- The hook approach replaces the prior pattern of passing `brainPath` as an explicit argument to each sub-agent. Do not mix the two patterns.
- Phase sequencing is implicit: the pre-hook always picks the first unstarted phase in declaration order. If a sub-agent runs more than once (e.g., retries), the hook will attempt to start the next unstarted phase — ensure phase names and ordering in brain.json match the actual invocation order.
- `jq -s '.[0] * .[1]'` does a shallow merge. Nested objects are replaced wholesale, not deeply merged. If a patch needs deep merge, the post-hook logic must be extended.
- Hook scripts must be executable (`chmod +x`). The allowed-tools list in the agent frontmatter must include `Bash(jq *)`, `Bash(rm -f *)`, and `Bash(export *)` for the orchestrator to create/delete brain.json and export the env var.
- The `DARK_FACTORY_WORK_DIR` env var is the sole coupling point between the orchestrator and the hook scripts. If this var is not exported before the first Agent tool call, all hooks will silently pass through.
