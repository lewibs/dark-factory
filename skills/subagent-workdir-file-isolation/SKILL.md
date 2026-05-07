---
name: subagent-workdir-file-isolation
description: "All file writes inside a sub-agent must be anchored to the explicit workDir parameter — never use bare relative paths, which resolve to the main repo CWD and contaminate the live branch."
user-invocable: false
---
## When to use

Every time you write or review a sub-agent (update-documentation-agent, skill-update-agent, debugger-agent, feature-agent, or any agent spawned by dark-factory-agent) that writes files to disk.

This applies to:
- Scratch/temporary files (e.g. `tmp/update-docs-flows.md`)
- Documentation files (e.g. `docs/docs/<flow>.md`)
- Skill files (e.g. `skills/<slug>/SKILL.md`)
- Any other artifact the agent is expected to land in the isolated worktree

## The root cause

Sub-agents run in their own process. The Bash tool's CWD defaults to the main repo root, not to the isolated worktree at `workDir`. A bare relative path like `docs/docs/foo.md` resolves against that CWD, so the write lands in the live main-branch directory instead of the feature branch worktree.

Two concrete instances of this bug, both fixed in 2026-05-06:
1. `update-documentation-agent` wrote `tmp/update-docs-flows.md` and `docs/docs/*.md` using bare relative paths. `workDir` was not even passed in the invocation args from dark-factory-agent.
2. `skill-update-agent` received `workDir` as input but built `skillPath = "skills/<slug>/SKILL.md"` as a relative string without joining it to `workDir`.

## Steps

**Step 1 — Resolve WORK_DIR at the top of the agent, before any file write.**

```
WORK_DIR = $DARK_FACTORY_WORK_DIR
if WORK_DIR is empty: WORK_DIR = contents of /tmp/dark-factory-work-dir (if the file exists)
if WORK_DIR is still empty: WORK_DIR = "." (fallback — log a warning: "WORK_DIR not set, writing to CWD")
```

**Step 2 — Prefix every file path with WORK_DIR.**

| Instead of | Use |
|---|---|
| `tmp/update-docs-flows.md` | `$WORK_DIR/tmp/update-docs-flows.md` |
| `docs/docs/<flow>.md` | `$WORK_DIR/docs/docs/<flow>.md` |
| `skills/<slug>/SKILL.md` | `$WORK_DIR/skills/<slug>/SKILL.md` |

**Step 3 — Ensure the orchestrator passes workDir in the invocation args.**

In dark-factory-agent (or any orchestrator), every `queue_batch_job` or `invoke` call to a file-writing sub-agent must include `workDir: WORK_DIR`:

```
queue_batch_job("update-documentation-agent", {planFilePath, workDir: WORK_DIR})
invoke skill-update-agent({planFilePath, workDir: WORK_DIR, taskSummary})
```

Without this the sub-agent cannot know which worktree to write into, even if it has WORK_DIR resolution logic.

**Step 4 — When reviewing a sub-agent for correctness, grep for bare relative writes:**

```bash
grep -n '^\s*\(write\|create\|build\|append\).*[^/]\(tmp\|docs\|skills\)/' agents/<dir>/agents/<agent>.md \
  | grep -v '\$WORK_DIR'
```

Any match without a `$WORK_DIR` prefix is a bug.

## Notes

- The WORK_DIR resolution block in this skill is identical to the one in `subagent-brain-patch-pointer-fallback`. That skill covers `brain-patch.json` writes specifically; this skill covers all other file writes. Both resolution sequences must appear in the same agent.
- For git operations (add/commit/push), use `git -C $WORK_DIR` — see skill `git-c-worktree-subagent`.
- For files that must land in the permanent project root (not the worktree), see skill `capture-project-dir-before-worktree`.
- The fallback `WORK_DIR = "."` prevents a hard crash but still produces wrong-location writes if neither env var nor pointer file is set. Always treat a missing WORK_DIR as a configuration error worth logging.
