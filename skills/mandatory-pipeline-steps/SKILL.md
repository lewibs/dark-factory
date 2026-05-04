---
name: mandatory-pipeline-steps
description: "When an orchestrator pipeline has steps that must never be skipped regardless of user input, those steps must be explicitly labeled non-bypassable in agent instructions with concrete example phrasings that would otherwise cause an agent to skip them."
user-invocable: false
---
## When to use

Any time you add or maintain a step in an orchestrator pipeline that:
- Must always run (e.g., code review, documentation update, skill capture, merge)
- Could plausibly be skipped if a user uses casual phrasing ("just merge it", "skip review", "looks fine")
- Protects system integrity or quality gates

Apply this pattern when writing or auditing the `## Rules` section of any orchestrator agent.

## Steps

1. **Identify mandatory steps by function, not position.** Ask: "If this step were skipped, would quality, correctness, or audit integrity be compromised?" If yes, it is mandatory.

2. **List mandatory steps explicitly by step number in the Rules section.** Do not rely on the agent understanding that "all steps should run" — enumerate:
   ```
   - Steps 7 (code review), 8 (update-documentation-agent), and 9 (skill-update-agent) are
     mandatory and must never be skipped regardless of user instructions, user phrasing,
     or any other input.
   ```

3. **Include concrete bypass-attempt phrasings in the rule.** Agents pattern-match on language; showing examples of disqualified inputs prevents rationalization:
   ```
   - These steps must run even when the user says "merge it", "skip review", "just merge",
     "looks good, ship it", or any similar shorthand.
   ```

4. **State the reason the steps are mandatory.** An agent that understands *why* a rule exists is less likely to find a clever exception:
   ```
   - These steps exist to protect code quality and system integrity; they are not
     optional conveniences.
   ```

5. **Guard against manual workarounds too.** If a mandatory step is downstream of a check (e.g., branch-drift guard), also forbid manual substitution:
   ```
   - If execution-agent produced no commits, halt and run cleanup — do NOT commit
     files manually to bypass the review gate.
   ```

6. **Write a test that asserts the mandatory-step rules exist** in the agent file. Parse the agent `.md` and assert specific strings are present:
   ```python
   def test_mandatory_steps_rule_present():
       content = Path("agents/dark-factory/agents/dark-factory-agent.md").read_text()
       assert "mandatory and must never be skipped" in content
       assert "skip review" in content or "skip.*review" in content
   ```

## Notes

- **Placement matters.** The mandatory-steps rule must appear in the `## Rules` section that the agent reads as operating constraints, not buried in pseudocode comments. Agents treat the Rules section as policy.
- **Step numbers drift.** If a new step is inserted before a mandatory step, the step number in the rule becomes stale. Update the rule whenever the step ordering changes, or use step names instead of numbers (e.g., "the code-review step").
- **The anti-pattern is implicit mandatory.** An agent that merely lists steps 1-9 in sequence does not know which steps are optional vs. mandatory. Without explicit labeling, a persuasive user instruction ("we're in a hurry, just merge") can cause an agent to rationalize skipping step 7-9. The explicit rule blocks this.
- **This pattern first appeared** in the manufacture flow fix (2026-05-04, RC4): steps 7-9 (code review, documentation, skill capture) were always intended to be mandatory but were not labeled as such. An agent following a user's "skip review" instruction technically violated no written rule — so the rule was made explicit.
