---
name: embed-absolute-output-path-in-handoff
description: "When a parent agent discovers items and dispatches sub-agents (via Task tool) to write files, always embed the absolute output file path in the handoff struct rather than letting the sub-agent reconstruct it from parts."
user-invocable: false
---
## When to use

When you are designing or modifying an agent that:
1. Discovers a list of items (systems, flows, components, etc.) at runtime, and
2. Invokes a sub-agent via the Task tool for each item to write a file to disk.

The sub-agent will not have access to the same runtime context (project_path, naming conventions, output directory) unless you explicitly pass it. Embed the resolved absolute path in the struct you hand off.

## Steps

1. In the parent agent's discovery step, resolve the full absolute output path for each item as soon as its name is known.
   - Pattern: `outputPath = "<project_path>/docs/docs/<item-slug>.md"` (constructed by the parent).
2. Include `outputPath` as a field in the handoff struct (e.g., `FlowInfo`, `SystemInfo`, or equivalent).
3. In the Task-tool prompt to the sub-agent, reference `outputPath` directly:
   ```
   Write your documentation to '<item.outputPath>'.
   Return the path to the file you wrote.
   ```
4. Do NOT instruct the sub-agent to derive the output path itself from a base directory and slug — it will not reliably reproduce the parent's naming logic.
5. Collect the returned path to confirm what was written; add it to the parent's `docs_written` (or equivalent) list.

## Notes

- The root cause of path mismatches in multi-agent pipelines is that sub-agents reconstruct paths independently and may use different slugging or casing logic. Pre-computing and embedding the path in the parent eliminates this class of bug entirely.
- This pattern was established when `init-docs-agent` was refactored from per-system to per-flow granularity: `FlowInfo.outputPath` is set by the parent as an absolute path so each `investigation-agent` invocation knows exactly where to write without needing `project_path` or the flow-name slug.
- If the output directory may not exist yet, the parent should `mkdir -p` it before dispatching any sub-agent calls — do not rely on sub-agents to create directories.
