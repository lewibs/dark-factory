---
name: stateless-command-agent-orchestrator
description: "How to build a thin command-agent orchestrator that passes state (planFilePath, prUrl, PROJECT_DIR) directly as local variables instead of through brain.json or hooks."
user-invocable: false
---
## When to use

When creating a new user-facing slash-command that routes to a single worker agent. Use this pattern instead of the brain-hook-driven-state pattern when:
- The command has a single clear worker (no classification needed)
- You do not need cross-agent phase gating via hooks
- State can be passed by direct return values rather than shared files

This is the architecture used by the six standalone commands: plan, execute, debug, repair, investigate, goto.

**Important:** Command agents do NOT manage worktrees. They run in-place — in whatever directory Claude Code is opened in. If the user needs to be in a specific worktree first, they invoke `/dark-factory:goto` before running a command. See the `gotoworktree-command` skill for that pattern.

## Steps

1. Create `commands/<name>.md` pointing to the command-agent:
   ```markdown
   ---
   description: "<one-liner>"
   ---
   Follow the instructions in `agents/dark-factory/agents/<name>-command-agent.md` exactly.
   ```
   Commands are auto-discovered from `commands/` — no `plugin.json` edits are needed.

2. Create `agents/dark-factory/agents/<name>-command-agent.md` with this skeleton.

   **For execute-type commands** (commands that produce code changes and a PR):
   ```
   <name>-command-agent(taskDescription, taskName):

     # Step 1 — derive taskName slug
     if taskName is empty:
       taskName = slugify(taskDescription)   # lowercase, hyphens, ≤30 chars

     # Step 2 — capture project dir (agent runs in-place; no worktree prep)
     PROJECT_DIR = bash("git rev-parse --show-toplevel")

     # Step 3 — invoke the single worker agent
     result = invoke <worker-agent>({ taskDescription, ... })
     if result is error: report error; STOP

     # Step 4 — post-execution pipeline (state passed directly, no brain.json)
     planFilePath = result.planPath  # or null for debug/repair routes
     invoke code-review-orchestrator-agent({ planFilePath, codePath: PROJECT_DIR })
     invoke update-documentation-agent({ planFilePath, workDir: PROJECT_DIR })
     try: invoke skill-update-agent({ planFilePath, workDir: PROJECT_DIR, taskSummary: taskDescription })
     WORK_DIR = bash("git rev-parse --show-toplevel")  # must be passed explicitly for pr-agent reuse
     prResult = invoke pr-agent({ planFilePath, workDir: WORK_DIR })
     prUrl = prResult.prUrl

     Report: "Done. PR: " + prUrl
     STOP
   ```

   **For plan-only commands** (commands that produce only a markdown plan file, no code changes — e.g. `/dark-factory:plan`):
   ```
   <name>-command-agent(taskDescription, taskName):

     # Step 1 — derive taskName slug
     ...

     # Step 2 — capture project dir
     PROJECT_DIR = bash("git rev-parse --show-toplevel")

     # Step 3 — invoke feature-agent with planOnly: true
     result = invoke feature-agent({ taskDescription, planOnly: true, ... })
     if result.status != "done": report result.status; STOP

     # Step 4 — plan-only: report planPath and stop.
     #   DO NOT run the post-execution pipeline (code-review, docs, skills, PR).
     #   Those steps apply only when code has actually changed.
     Report: "Plan approved. File: " + result.planPath
     STOP
   ```

   **For read-only/investigate commands** (no code changes, no plan file): delegate directly to the worker and report the output path. No pipeline steps.

3. No brain.json is created, no hooks inject state, no `/tmp/dark-factory-work-dir` pointer is written. State flows directly through agent return values.

4. The `skill-update-agent` step is non-fatal — always wrap in try/catch and continue on failure.

5. For the `investigate` command (read-only, no code changes), skip the pipeline entirely: just delegate to `investigation-orchestrator` directly and report the doc path.

6. There is no branch drift guard and no cleanup step — the command agent does not own the worktree lifecycle.

## Notes

- `planFilePath` may be `null` for debug and repair routes (no plan file generated). When null, pass a human-readable string like `"Task: " + taskDescription` to code-review-orchestrator-agent and pr-agent so they have context.
- **Do not add the post-execution pipeline to plan-only commands.** The pipeline (code-review → docs → skills → PR) only makes sense when code has actually changed. A plan-only command produces a single markdown file; adding the pipeline causes phantom code reviews, spurious PRs, and skill extractions against no real code change. The canonical division: `plan` command = feature-agent with planOnly:true, no pipeline. `execute` command = execution-agent + full pipeline.
- **Never gate the post-execution pipeline on a worker flag.** A worker agent must never return a `significantChange` (or similar boolean) that the command-agent uses to skip code review or PR steps. The pipeline always runs after a successful worker result — pr-agent internally decides whether to open a new PR or reuse an existing one on the current branch (via `gh pr view`). Adding a significance gate breaks PR reuse: re-runs on an existing branch will skip pr-agent and the existing PR will never be updated.
- **Always pass `workDir` explicitly to pr-agent.** pr-agent uses `gh pr view` on the current branch to detect existing PRs and decide between creation and reuse. Without `workDir`, `gh` may resolve to the wrong repo context. Always resolve `WORK_DIR = bash("git rev-parse --show-toplevel")` immediately before the pr-agent invocation and pass it as the `workDir` argument.
- Command agents no longer call `prep-feature-dir.sh`, `find-related-pr.sh`, `AskUserQuestion` for PR reuse, or `cleanup-worktree.sh`. All of that is handled by `gotoworktree-command-agent` when the user explicitly needs a worktree.
- `codePath` and `workDir` passed to post-execution agents are `PROJECT_DIR` (the live cwd), not a separate `WORK_DIR`. If the user is already inside a worktree, `PROJECT_DIR` will resolve to the worktree root correctly.
- Do not add the command to an agent allowlist or PHASE_MAP in any hook — this pattern uses no hooks.
