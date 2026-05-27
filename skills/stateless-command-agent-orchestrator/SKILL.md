---
name: stateless-command-agent-orchestrator
description: "How to build a thin command-agent orchestrator that passes state (planFilePath, prUrl, WORK_DIR) directly as local variables instead of through brain.json or hooks."
user-invocable: false
---
## When to use

When creating a new user-facing slash-command that routes to a single worker agent. Use this pattern instead of the brain-hook-driven-state pattern when:
- The command has a single clear worker (no classification needed)
- You do not need cross-agent phase gating via hooks
- State can be passed by direct return values rather than shared files

This is the architecture used by the five standalone commands: plan, execute, debug, repair, investigate.

## Steps

1. Create `commands/<name>.md` pointing to the command-agent:
   ```markdown
   ---
   description: "<one-liner>"
   ---
   Follow the instructions in `agents/dark-factory/agents/<name>-command-agent.md` exactly.
   ```
   Commands are auto-discovered from `commands/` — no `plugin.json` edits are needed.

2. Create `agents/dark-factory/agents/<name>-command-agent.md` with this skeleton:
   ```
   <name>-command-agent(taskDescription, taskName):

     # Step 1 — derive taskName slug
     if taskName is empty:
       taskName = slugify(taskDescription)   # lowercase, hyphens, ≤30 chars

     # Step 2 — PR reuse check (find-related-pr.sh) + worktree prep
     PROJECT_DIR = bash("git rev-parse --show-toplevel")
     relatedPrOutput = bash("bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/find-related-pr.sh\" \"$taskDescription\"") || ""
     EXISTING_BRANCH = extract BRANCH= from relatedPrOutput
     if EXISTING_BRANCH is not empty:
       answer = AskUserQuestion("Reuse existing branch or create fresh?", ...)
       USE_EXISTING = (answer == "Reuse existing branch")
     else:
       USE_EXISTING = false

     if USE_EXISTING:
       existingTaskName = EXISTING_BRANCH after stripping "<prefix>/" prefix
       WORK_DIR = PROJECT_DIR + "/../" + basename(PROJECT_DIR) + "-" + existingTaskName
       if worktree does not exist:
         bash("git -C \"$PROJECT_DIR\" worktree add \"$WORK_DIR\" \"$EXISTING_BRANCH\"")
       taskName = existingTaskName
       branchRef = EXISTING_BRANCH
     else:
       prepOutput = bash("bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/prep-feature-dir.sh\" \"$taskName\"")
       WORK_DIR = extract WORK_DIR=<value> from prepOutput
       if script fails: STOP (no cleanup needed)
       branchRef = "feature/" + taskName

     # Step 3 — invoke the single worker agent
     result = invoke <worker-agent>({ taskDescription, ... })
     if result is error: run cleanup(WORK_DIR, taskName); STOP

     # Step 4 — branch drift guard
     driftCheck = bash("git -C \"$WORK_DIR\" log main..<branchRef> --oneline 2>&1")
     if driftCheck is empty: run cleanup(WORK_DIR, taskName); STOP

     # Step 5 — post-execution pipeline (state passed directly, no brain.json)
     planFilePath = result.planPath  # or null for debug/repair routes
     invoke code-review-orchestrator-agent({ planFilePath, codePath: WORK_DIR })
     invoke update-documentation-agent({ planFilePath, workDir: WORK_DIR })
     try: invoke skill-update-agent({ planFilePath, workDir: WORK_DIR, taskSummary: taskDescription })
     prResult = invoke pr-agent({ planFilePath })
     prUrl = prResult.prUrl

     # Step 6 — cleanup (no brain.json to delete)
     bash("bash \"${CLAUDE_PLUGIN_ROOT}/agents/dark-factory/scripts/cleanup-worktree.sh\" \"$WORK_DIR\" \"$taskName\"")

     Report: "Done. PR: " + prUrl
     STOP
   ```

3. No brain.json is created, no hooks inject state, no `/tmp/dark-factory-work-dir` pointer is written. State flows directly through agent return values.

4. The `skill-update-agent` step is non-fatal — always wrap in try/catch and continue on failure.

5. For the `investigate` command (read-only, no code changes), skip steps 2-6 entirely: just delegate to `investigation-orchestrator` directly and report the doc path.

## Notes

- `planFilePath` may be `null` for debug and repair routes (no plan file generated). When null, pass a human-readable string like `"Task: " + taskDescription` to code-review-orchestrator-agent and pr-agent so they have context.
- The cleanup script (`cleanup-worktree.sh`) removes the entire worktree directory. Always run it on both success and error paths (except on prep failure — no worktree exists yet).
- The branch drift guard must use `branchRef` (the full branch name including any prefix), not the hardcoded string `"feature/" + taskName`. When reusing an existing PR the branch may have any prefix (bugfix/, plain slug, etc.) — hardcoding `feature/` causes the drift check to evaluate the wrong branch and always fail.
- Do not add the command to an agent allowlist or PHASE_MAP in any hook — this pattern uses no hooks.
