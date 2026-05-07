---
name: enable-prompt-caching-on-agents
description: "Add cache-control: ephemeral to agent YAML frontmatter to enable Claude Code prompt caching and reduce system prompt token costs by ~90% on high-frequency agents."
user-invocable: false
---
## When to use

Use this skill when a new agent is added to the codebase and becomes high-frequency (many runs in `metrics.csv`), or when a cost-reduction pass is needed across existing agents. Apply whenever `metrics.csv` shows an agent accumulating significant `sum_tokens` or `runs`.

## Steps

1. Identify target agents by querying `metrics.csv`. Sort by `runs` (or `sum_tokens`) descending. Focus on agents with the highest invocation count — these benefit most from caching.

2. For each target agent `.md` file, add `cache-control: ephemeral` to the YAML frontmatter, immediately after the `model:` line:

   ```yaml
   ---
   name: my-agent
   user-invocable: false
   model: haiku
   cache-control: ephemeral
   ---
   ```

3. No other code changes are needed. Claude Code reads this field at spawn time and applies prompt caching automatically.

## Notes

- The field must be in the YAML frontmatter block (between the `---` delimiters), not in the agent body.
- Placement after `model:` is conventional; the exact line order within the frontmatter does not affect behavior.
- `ephemeral` is the only supported value for `cache-control` in Claude Code agent files.
- Prompt caching cuts system-prompt token costs by approximately 90% for repeated invocations of the same agent. It has no effect on input/output tokens for the task body itself.
- Only agents invoked repeatedly (orchestrators, reviewers, documentation updaters, execution agents) benefit meaningfully. One-shot or rare agents are not worth targeting.
- The target set from this initial pass: `feature-agent`, `code-review-orchestrator-agent`, `update-documentation-agent`, `skill-update-agent`, `execution-agent`.
