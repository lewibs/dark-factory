---
name: subagent-brain-patch-pointer-fallback
description: "When a sub-agent writes brain-patch.json, it must resolve WORK_DIR via the /tmp/dark-factory-work-dir pointer file because $DARK_FACTORY_WORK_DIR is never propagated to sub-agent processes."
user-invocable: false
---
## When to use

Every time a sub-agent (feature-agent, pr-agent, skill-update-agent, update-documentation-agent, debugger-agent, or any new agent added to the pipeline) needs to write `brain-patch.json` at the end of its run.

Do NOT use the bare `$DARK_FACTORY_WORK_DIR` approach without the pointer-file fallback. The env var is set by the orchestrator (dark-factory-agent) in one Bash subprocess and is never visible to sub-agents, which run in isolated processes.

## The root cause

`DARK_FACTORY_WORK_DIR` is exported by the orchestrator inside a Bash tool call. That call's subprocess exits immediately after, taking the env var with it. Sub-agents launched later (via the `Agent` tool) run in their own fresh environment and never inherit the value.

`/tmp/dark-factory-work-dir` is written to disk by the orchestrator and survives across process boundaries, making it the correct resolution channel.

## Steps

In every sub-agent's brain-patch.json write block, use this exact resolution sequence:

```
WORK_DIR = $DARK_FACTORY_WORK_DIR
if WORK_DIR is empty: WORK_DIR = contents of /tmp/dark-factory-work-dir (if the file exists)
if WORK_DIR is still empty: skip writing the patch silently
else: write $WORK_DIR/brain-patch.json with the sub-agent's output fields
```

In pseudocode / shell:

```bash
WORK_DIR="${DARK_FACTORY_WORK_DIR:-}"
if [ -z "$WORK_DIR" ] && [ -f /tmp/dark-factory-work-dir ]; then
  WORK_DIR=$(cat /tmp/dark-factory-work-dir)
fi
if [ -n "$WORK_DIR" ]; then
  echo '{ "myField": "value" }' > "$WORK_DIR/brain-patch.json"
fi
```

## Notes

- This pattern is required for ALL five existing brain-patch writers and any new sub-agent added to the pipeline.
- The pointer file is created by dark-factory-agent immediately after `brain.json` is written (see `brain-hook-driven-state` skill, Step 2) and deleted during cleanup.
- Hook scripts (pre/post tool-use) use the same pointer-file fallback on the bash side — see `claude-code-hook-env-isolation` skill for the hook-specific pattern.
- Never silently skip the write without first checking the pointer file — silent skips mean brain.json fields (`planFilePath`, `prUrl`, `docsWritten`, `skillsWritten`, `bugFiles`) are never populated and the orchestrator cannot hand values between pipeline phases.
