---
name: capture-project-dir-before-worktree
description: "How to safely capture the real project root path before entering a worktree, so that files written at end-of-manufacture land in the permanent project directory rather than the (deleted) worktree."
user-invocable: false
---
## When to use

Whenever a manufacture step needs to write a permanent file (metrics CSV, report, artifact, etc.) to the real project root at the end of a manufacture run — specifically in the cleanup step of dark-factory-agent, after sub-agents have run and before the worktree is deleted.

## Steps

1. Before `prep-feature-dir.sh` is called (while the shell cwd is still the real project root), capture PROJECT_DIR:
   ```bash
   PROJECT_DIR=$(git rev-parse --show-toplevel)
   ```

2. Store PROJECT_DIR into brain.json at creation time so it is available in the cleanup step:
   ```json
   {
     "projectDir": "<PROJECT_DIR>",
     "workDir": "<WORK_DIR>",
     ...
   }
   ```

3. In the cleanup step, read PROJECT_DIR from brain.json **before** deleting brain.json:
   ```bash
   PROJECT_DIR=$(jq -r '.projectDir' "$WORK_DIR/brain.json")
   python3 scripts/update-metrics.py --csv "$PROJECT_DIR/metrics.csv" --brain "$WORK_DIR/brain.json" || true
   rm -f "$WORK_DIR/brain.json"
   bash agents/dark-factory/scripts/cleanup-worktree.sh ...
   ```

4. Never use `brain.json.workDir` as the base path for permanent files. The worktree at `workDir` is deleted by `cleanup-worktree.sh`, so any write to `$workDir/foo` after cleanup is silently lost.

## Notes

- `brain.json.workDir` and `brain.json.projectDir` serve different purposes: `workDir` is the ephemeral git worktree; `projectDir` is the permanent repo root that persists across sessions.
- `git rev-parse --show-toplevel` must be run from the real project working directory, not from inside the worktree. Capture it in the same shell block that initializes brain.json, before `cd`-ing into the worktree.
- The allowed-tools list in dark-factory-agent's frontmatter must include `Bash(git rev-parse *)` for this to work.
- This pattern applies to any file that should persist after manufacture: metrics CSVs, changelog appends, deployment records, etc.
