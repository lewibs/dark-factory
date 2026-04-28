---
name: claude-code-hook-env-isolation
description: "Env vars set via `export` inside a Claude Code Bash tool call are invisible to PreToolUse/PostToolUse hook processes — use a pointer file at a fixed path as the fallback channel instead."
user-invocable: false
---
## When to use

Whenever a hook script needs a value (e.g. a working directory path) that the LLM agent sets during a manufacture run. This pattern is required any time you are tempted to write `export SOME_VAR=<value>` inside a Bash tool call and expect hook scripts to see it.

## The problem

Claude Code hooks run as direct children of the Claude Code process. They inherit Claude Code's environment — NOT the environment of any LLM Bash tool call. When the LLM calls:

```bash
export DARK_FACTORY_WORK_DIR=/some/worktree
```

that `export` lives only in the Bash subprocess that ran the tool call. When that subprocess exits, the env var is gone. The Claude Code parent process never sees it. Hook subprocesses therefore never see it either.

This is a fundamental OS constraint: a child process cannot modify its parent's environment.

## Fix: pointer file fallback

Write the value to a well-known file at a fixed path immediately after you would have set the env var. Hook scripts read this file as a fallback when the env var is unset.

### LLM agent (orchestrator) side

```bash
# Write brain.json first, then write the pointer file alongside it.
echo "/absolute/path/to/worktree" > /tmp/dark-factory-work-dir

# At cleanup, delete the pointer file BEFORE removing the worktree.
rm -f /tmp/dark-factory-work-dir
rm -f $WORK_DIR/brain.json
```

The `export DARK_FACTORY_WORK_DIR=...` line can be kept for local development where the
value IS pre-loaded into Claude Code's environment (e.g., via `~/.profile`). The pointer
file is the authoritative fallback for the common in-process case.

### Hook script side

Add this block near the top of every hook that needs `DARK_FACTORY_WORK_DIR`, before any reference to `$BRAIN_PATH` or similar:

```bash
DARK_FACTORY_POINTER_FILE="/tmp/dark-factory-work-dir"
if [ -z "${DARK_FACTORY_WORK_DIR:-}" ] && [ -f "$DARK_FACTORY_POINTER_FILE" ]; then
  DARK_FACTORY_WORK_DIR=$(cat "$DARK_FACTORY_POINTER_FILE")
  echo "my-hook | pointer-file | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR}" >&2
fi
```

This must appear in both `pre-tool-use-hook.sh` and `post-tool-use-hook.sh`.

## Why `/tmp/`

- Always writable by the current user.
- Cleaned by the OS on reboot, providing automatic safety if the cleanup step fails.
- `~/.dark-factory-work-dir` is an acceptable alternative but requires home-dir expansion.

## Notes

- This constraint affects ANY env var an LLM tries to set for hook consumption, not just `DARK_FACTORY_WORK_DIR`. The pointer-file pattern generalises: one file per value, fixed path, cleaned up at the end of the run.
- If you are writing a new env var that hooks must see, do not rely on `export` alone. Always pair it with a pointer file.
- The `brain-hook-driven-state` skill references this pattern; see its Step 2 for the orchestrator write and its cleanup step for the delete.
- Tested in `tests/test_metrics_env_isolation.py`, which simulates hook subprocess execution with and without the pointer file.
