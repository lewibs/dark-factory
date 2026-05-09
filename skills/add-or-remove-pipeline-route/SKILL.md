---
name: add-or-remove-pipeline-route
description: "Checklist of every file that must be updated in lockstep when adding or removing a top-level pipeline route (e.g. feature, debugger, repair) from dark-factory."
user-invocable: false
---
## When to use

When adding a new top-level pipeline route to dark-factory (e.g., a new orchestrator that dark-factory-agent can dispatch to), or when deleting an existing route. The route enum and the phase-agent allowlist are duplicated across many files; missing any one of them causes silent breakage.

## Steps

1. **Hook scripts** — Update the `PHASE_AGENTS` pipe-delimited string in BOTH:
   - `agents/dark-factory/scripts/pre-tool-use-hook.sh`
   - `agents/dark-factory/scripts/post-tool-use-hook.sh`
   Add the new orchestrator's `subagent_type` value, or remove the deleted one. These two files must always be in sync.

2. **task-classifier skill** — `skills/task-classifier/SKILL.md`
   - Update the `"classification"` union type in the Classification Result JSON example.
   - Add or remove the route's entry from the `"options"` array in the Ambiguous Result example.
   - Add or remove the route's `### <route-name>` description section.

3. **brain-state-manager skill** — `skills/brain-state-manager/SKILL.md`
   - Update the `classification` parameter description to list current valid values.

4. **route-specific-agent-behavior skill** — `skills/route-specific-agent-behavior/SKILL.md`
   - Update the description frontmatter to list current routes.
   - Update the `## When to use` section.
   - Add or remove the branch for the route in Step 2 of the skill body.

5. **pr-agent** — `agents/pr/agents/pr-agent.md`
   - Find the `ELSE IF classification ==` chain and add/remove the route branch.

6. **manufacture command** — `commands/manufacture.md`
   - Update the `description` frontmatter string (lists routes inline).
   - Add or remove the `- "<route>" → invoke <orchestrator>(...)` dispatch line in the routing table.

7. **dark-factory-agents doc** — `docs/docs/dark-factory-agents.md`
   - Update the Mermaid `flowchart TD` diagram to add/remove the route edge and any sub-agent nodes.
   - Update the `dark-factory-agent` bullet's `Invokes:` list.
   - Update the `task-classifier` bullet's `Role:` description (lists route count).
   - Add or remove the entire `### Flow: <route>` section with all sub-agent entries.
   - If removing, remove the route from the Skills table rows that list which agent uses them.

8. **docs/docs/README.md** — Update if it lists pipeline routes inline.

9. **phase-agent-allowlist skill** — `skills/phase-agent-allowlist/SKILL.md`
   - Update the `PHASE_AGENTS` example string in Step 1 to match the new set.

## Notes

- The `PHASE_AGENTS` regex in hook scripts uses anchored matching (`^($PHASE_AGENTS)$`), so the string value must exactly match the `subagent_type` argument passed to the Agent tool — which is the agent's `name:` frontmatter field (e.g., `feature-agent`, not `feature_agent`).
- When adding a route, also create the agent file(s) under `agents/<route>/agents/` and list any new skills in the Skills table in `dark-factory-agents.md`.
- When removing a route, verify no other agent still references the deleted orchestrator as a spawner (search for its name in all `.md` files under `agents/`).
- Failing to update both hook scripts simultaneously is the most common mistake: the pre-hook sets a phase running but the post-hook never marks it complete, leaving brain.json in a permanently "running" state for that phase.
