"""
Regression tests for agent flow deviation when manufacture is invoked from a nested
Claude session (bug: 2026-05-08-agent-flow-deviation-nested-session).

Two failure modes:
1. commands/manufacture.md uses a relative path to dark-factory-agent.md that breaks
   when CWD differs from the plugin install root (e.g., nested session with host project CWD).
2. create-pr/SKILL.md description says "manage it through to merge", providing merge
   scripts in its table and no explicit no-merge rule, allowing callers to bypass pr-agent
   and perform a manual merge.

See: docs/bugs/2026-05-08-agent-flow-deviation-nested-session.md

Flow: agentFlowDeviationNestedSession
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MANUFACTURE_CMD_PATH = os.path.join(PROJECT_ROOT, "commands", "manufacture.md")
DARK_FACTORY_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "dark-factory", "agents", "dark-factory-agent.md"
)
PR_AGENT_PATH = os.path.join(PROJECT_ROOT, "agents", "pr", "agents", "pr-agent.md")
CREATE_PR_SKILL_PATH = os.path.join(PROJECT_ROOT, "skills", "create-pr", "SKILL.md")


def _full(path: str) -> str:
    with open(path) as f:
        return f.read()


def _body(path: str) -> str:
    """Return the body of a file (everything after the closing front-matter ---)."""
    content = _full(path)
    fm_end = content.find("\n---", 4)
    return content[fm_end + 4:] if fm_end != -1 else content


# ---------------------------------------------------------------------------
# RC1 — manufacture.md must use an absolute or plugin-root-anchored path
# ---------------------------------------------------------------------------

class TestManufactureCmdPath:
    """
    agentFlowDeviationNestedSession — commands/manufacture.md must invoke
    dark-factory-agent as a sub-agent via the Agent tool, not via file path reference.
    This prevents CWD-dependent resolution failures in nested sessions.
    """

    def test_manufacture_cmd_does_not_use_bare_relative_path(self):
        """
        agentFlowDeviationNestedSession.manufacture-no-bare-relative-path:
        commands/manufacture.md must NOT reference dark-factory-agent.md with a bare
        relative path like `agents/dark-factory/agents/dark-factory-agent.md`.

        When /dark-factory:manufacture is invoked from a nested Claude session (e.g., via
        the Skill tool from a depth-2+ agent), the CWD may be the host project root, not the
        plugin install directory. A bare relative path then fails to resolve, and the caller
        falls back to invoking the subagent type directly, bypassing the normal dispatch flow.

        The proper solution is to invoke dark-factory-agent as a sub-agent using the Agent
        tool with agent: "dark-factory-agent", which doesn't depend on CWD-relative paths.

        If this test fails: commands/manufacture.md still uses a bare relative path for
        dark-factory-agent.md — replace it with an Agent tool invocation.
        # Plan path: agentFlowDeviationNestedSession.manufacture-no-bare-relative-path
        """
        content = _full(MANUFACTURE_CMD_PATH)
        # Bare relative path pattern: starts with "agents/" without ${CLAUDE_PLUGIN_ROOT}
        bare_relative = re.search(
            r'`agents/dark-factory/agents/dark-factory-agent\.md`',
            content,
        )
        assert bare_relative is None, (
            "commands/manufacture.md must NOT reference dark-factory-agent.md with a bare "
            "relative path ('agents/dark-factory/agents/dark-factory-agent.md'). "
            "When invoked from a nested Claude session, this path fails to resolve because "
            "CWD is not the plugin root. Use the Agent tool to invoke dark-factory-agent by name: "
            "`invoke Agent({ agent: \"dark-factory-agent\", prompt: ... })`"
        )

    def test_manufacture_cmd_uses_agent_tool(self):
        """
        agentFlowDeviationNestedSession.manufacture-uses-agent-tool:
        commands/manufacture.md must invoke dark-factory-agent as a sub-agent using the
        Agent tool, rather than using a file path reference (which breaks in nested sessions).

        Using the Agent tool with agent: "dark-factory-agent" resolves the agent by name,
        which is CWD-independent and works correctly in nested sessions.

        If this test fails: commands/manufacture.md does not use the Agent tool to invoke
        dark-factory-agent — update it to use invoke Agent({ agent: "dark-factory-agent" ... }).
        # Plan path: agentFlowDeviationNestedSession.manufacture-uses-agent-tool
        """
        content = _full(MANUFACTURE_CMD_PATH)
        uses_agent_tool = re.search(
            r'invoke\s+Agent\s*\(\s*\{\s*agent\s*:\s*["\']dark-factory-agent["\']',
            content,
        )
        assert uses_agent_tool is not None, (
            "commands/manufacture.md must invoke dark-factory-agent as a sub-agent using "
            "the Agent tool. This approach is CWD-independent and works in nested sessions. "
            "Example: `invoke Agent({ agent: \"dark-factory-agent\", prompt: ... })`"
        )


# ---------------------------------------------------------------------------
# RC2 — create-pr/SKILL.md must not imply merge authorization
# ---------------------------------------------------------------------------

class TestCreatePrSkillNoMergeImplication:
    """
    agentFlowDeviationNestedSession — create-pr/SKILL.md must not describe itself
    as managing a PR "through to merge" and must have an explicit no-merge rule,
    so callers cannot interpret it as authorizing a manual merge.
    """

    def test_create_pr_skill_description_does_not_say_through_to_merge(self):
        """
        agentFlowDeviationNestedSession.create-pr-no-merge-description:
        create-pr/SKILL.md must NOT say "manage it through to merge" or equivalent
        in its description or heading.

        The current description says "Open a pull request on GitHub and manage it through
        to merge." This allows an agent that reads the skill directly (bypassing pr-agent)
        to interpret it as authorization to merge. The skill must be scoped to PR opening only.

        If this test fails: create-pr/SKILL.md still says "manage it through to merge" —
        update the description to say the skill opens the PR and stops; merging is not part
        of create-pr's responsibility.
        # Plan path: agentFlowDeviationNestedSession.create-pr-no-merge-description
        """
        content = _full(CREATE_PR_SKILL_PATH)
        through_to_merge = re.search(
            r'(?i)manage it through to merge|through to merge',
            content,
        )
        assert through_to_merge is None, (
            "create-pr/SKILL.md must NOT say 'manage it through to merge'. "
            "This description allows callers to interpret the skill as authorizing a full "
            "merge workflow, bypassing pr-agent's no-merge constraint. "
            "Update the description to: 'Opens a pull request on GitHub. Does not merge.' "
            "Merge scripts in the Scripts table should be removed or moved to a separate reference."
        )

    def test_create_pr_skill_has_no_merge_rule(self):
        """
        agentFlowDeviationNestedSession.create-pr-explicit-no-merge-rule:
        create-pr/SKILL.md Rules section must contain an explicit "do not merge" rule.

        Without an explicit rule, any agent that reads create-pr/SKILL.md directly can
        interpret the merge scripts in the Scripts table as permission to merge. The rule
        closes this gap by making the no-merge constraint visible at the skill level.

        If this test fails: create-pr/SKILL.md Rules section does not say "do not merge"
        — add an explicit rule: "Do not merge. Merging is handled by the caller after
        pr-agent returns status: ready."
        # Plan path: agentFlowDeviationNestedSession.create-pr-explicit-no-merge-rule
        """
        content = _full(CREATE_PR_SKILL_PATH)
        # Look in the Rules section
        rules_section = re.search(r'## Rules\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
        if rules_section is None:
            pytest.fail(
                "create-pr/SKILL.md must have a ## Rules section containing an explicit "
                "'do not merge' rule."
            )
        rules_text = rules_section.group(1)
        has_no_merge_rule = re.search(
            r'(?i)do not merge|never merge|not merge',
            rules_text,
        )
        assert has_no_merge_rule is not None, (
            "create-pr/SKILL.md Rules section must contain an explicit 'do not merge' rule. "
            "Without it, agents reading the skill directly (bypassing pr-agent) can interpret "
            "the merge scripts in the Scripts table as permission to merge. "
            "Add: '- Do not merge. Merging is out of scope for this skill.'"
        )

    def test_create_pr_skill_scripts_table_does_not_include_merge_script(self):
        """
        agentFlowDeviationNestedSession.create-pr-no-merge-script:
        create-pr/SKILL.md Scripts table must not contain merge-related commands
        (gh pr merge, git merge) that could be interpreted as part of the skill's scope.

        If this test fails: the Scripts table still includes merge commands — remove them
        or move them to a reference-only section explicitly labeled as out of scope.
        # Plan path: agentFlowDeviationNestedSession.create-pr-no-merge-script
        """
        content = _full(CREATE_PR_SKILL_PATH)
        merge_script = re.search(
            r'(?i)gh pr merge|git merge\b',
            content,
        )
        assert merge_script is None, (
            "create-pr/SKILL.md Scripts table must not include merge commands (gh pr merge, "
            "git merge). These commands imply that merging is part of the skill's scope, "
            "which contradicts pr-agent's no-merge constraint. Remove merge-related rows "
            "from the Scripts table."
        )


# ---------------------------------------------------------------------------
# RC3 — dark-factory-agent must not allow caller to merge after pr-agent returns ready
# ---------------------------------------------------------------------------

class TestDarkFactoryAgentNoManualMerge:
    """
    agentFlowDeviationNestedSession — dark-factory-agent.md must not allow a caller
    to merge after pr-agent returns status: ready.
    """

    def test_dark_factory_agent_rules_forbid_manual_merge(self):
        """
        agentFlowDeviationNestedSession.dark-factory-agent-no-manual-merge:
        dark-factory-agent.md Rules section must contain an explicit prohibition against
        merging or performing any PR lifecycle steps manually after pr-agent returns.

        When a caller receives pr-agent's `status: ready`, there is nothing in
        dark-factory-agent.md preventing it from proceeding to merge manually. An explicit
        rule closes this gap.

        If this test fails: dark-factory-agent.md Rules does not forbid manual merge —
        add: "FORBIDDEN: Never merge a PR manually. pr-agent returns status:ready but does
        not merge. Merging is the developer's responsibility after review."
        # Plan path: agentFlowDeviationNestedSession.dark-factory-agent-no-manual-merge
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        # Look for a rule forbidding manual merge
        has_no_merge_rule = re.search(
            r'(?i)(FORBIDDEN|never|do not).*merge.*PR|merge.*PR.*(FORBIDDEN|never|do not)',
            content,
        )
        assert has_no_merge_rule is not None, (
            "dark-factory-agent.md must contain an explicit FORBIDDEN rule against merging "
            "a PR manually. pr-agent returns status:ready but does not merge — the developer "
            "is responsible for merging. Without an explicit rule, callers can proceed to "
            "merge manually after pr-agent returns. "
            "Add to Rules: 'FORBIDDEN: Never merge a PR manually or instruct any sub-agent "
            "to merge. pr-agent stops at status:ready. Merging is the developer\\'s responsibility.'"
        )
