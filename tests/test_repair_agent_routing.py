"""
Regression tests for: repair-implementation-agent not found.

Root cause:
  PR #96 renamed repair-implementation-agent.md to repair-agent.md but did not update all
  routing references. Two skill files (branch-drift-guard/SKILL.md and
  git-c-worktree-subagent/SKILL.md) retained stale references to repair-implementation-agent.
  These stale references are a regression risk — an LLM agent following those skill docs
  to update routing would re-introduce the broken agent name.

  The primary routing reference in dark-factory-agent.md was already fixed by commit 6a66c8c,
  but the skill files were missed.

See: docs/bugs/2026-05-07-repair-implementation-agent-not-found.md
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DARK_FACTORY_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "dark-factory", "agents", "dark-factory-agent.md"
)
BRANCH_DRIFT_GUARD_SKILL_PATH = os.path.join(
    PROJECT_ROOT, "skills", "branch-drift-guard", "SKILL.md"
)
GIT_C_WORKTREE_SKILL_PATH = os.path.join(
    PROJECT_ROOT, "skills", "git-c-worktree-subagent", "SKILL.md"
)
REPAIR_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "repair", "agents", "repair-agent.md"
)
STALE_REPAIR_IMPL_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "repair", "agents", "repair-implementation-agent.md"
)


def _body(path: str) -> str:
    """Return the body of an agent/skill file (everything after the closing front-matter ---)."""
    with open(path) as f:
        content = f.read()
    fm_end = content.find("\n---", 4)
    return content[fm_end + 4:] if fm_end != -1 else content


def _full(path: str) -> str:
    with open(path) as f:
        return f.read()


class TestRepairAgentFileExists:
    """Verify repair-agent.md exists at the correct path and no stale implementation agent file exists."""

    def test_repair_agent_file_exists(self):
        """
        repairAgentRouting.agent-file-exists: repair-agent.md must exist at
        agents/repair/agents/repair-agent.md.

        If this test fails: the repair worker agent file is missing — any repair task will fail
        with 'Agent type not found'.
        # Plan path: repairAgentRouting.agent-file-exists
        """
        assert os.path.isfile(REPAIR_AGENT_PATH), (
            f"repair-agent.md must exist at {REPAIR_AGENT_PATH}. "
            "Without this file, the repair route cannot function."
        )

    def test_repair_implementation_agent_file_does_not_exist(self):
        """
        repairAgentRouting.stale-file-absent: repair-implementation-agent.md must NOT exist.

        The file was renamed to repair-agent.md in PR #96. If the old name still exists,
        it creates ambiguity and may cause old routing references to silently succeed,
        making future renames harder to detect.
        # Plan path: repairAgentRouting.stale-file-absent
        """
        assert not os.path.isfile(STALE_REPAIR_IMPL_AGENT_PATH), (
            f"repair-implementation-agent.md must NOT exist at {STALE_REPAIR_IMPL_AGENT_PATH}. "
            "This file was renamed to repair-agent.md in PR #96. Its presence suggests an incomplete rename."
        )


class TestDarkFactoryAgentRoutesCorrectly:
    """Verify dark-factory-agent.md uses repair-agent (not repair-implementation-agent)."""

    def test_dark_factory_agent_routes_to_repair_agent(self):
        """
        repairAgentRouting.dfa-routes-repair-agent: dark-factory-agent.md must invoke
        repair-agent, not repair-implementation-agent.

        If this test fails: the main orchestrator is routing repair tasks to a non-existent
        agent, causing 'Agent type not found' errors for all repair tasks.
        # Plan path: repairAgentRouting.dfa-routes-repair-agent
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        assert re.search(r"(?i)invoke\s+repair-agent\b", body), (
            "dark-factory-agent.md must contain 'invoke repair-agent' to route repair tasks. "
            "If it references repair-implementation-agent, the Agent tool will fail with 'not found'."
        )

    def test_dark_factory_agent_does_not_reference_repair_implementation_agent(self):
        """
        repairAgentRouting.dfa-no-stale-ref: dark-factory-agent.md must NOT reference
        repair-implementation-agent anywhere.

        If this test fails: the orchestrator has a stale reference that will cause
        'Agent type not found' at runtime for all repair-classified tasks.
        # Plan path: repairAgentRouting.dfa-no-stale-ref
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        assert "repair-implementation-agent" not in content, (
            "dark-factory-agent.md must NOT reference repair-implementation-agent. "
            "The agent was renamed to repair-agent in PR #96. "
            "Remove all occurrences of repair-implementation-agent from this file."
        )


class TestSkillFilesUseCorrectAgentName:
    """Verify skill files reference repair-agent, not repair-implementation-agent."""

    def test_branch_drift_guard_uses_repair_agent(self):
        """
        repairAgentRouting.branch-drift-guard-name: branch-drift-guard/SKILL.md must reference
        repair-agent (not repair-implementation-agent) in its list of worker agents.

        If this test fails: the skill doc names a non-existent agent. An LLM following this
        skill to update orchestrator routing would re-introduce the broken agent reference.
        # Plan path: repairAgentRouting.branch-drift-guard-name
        """
        content = _full(BRANCH_DRIFT_GUARD_SKILL_PATH)
        assert "repair-implementation-agent" not in content, (
            "branch-drift-guard/SKILL.md must NOT reference repair-implementation-agent. "
            "The agent was renamed to repair-agent. Update the worker agent list to use repair-agent."
        )

    def test_branch_drift_guard_mentions_repair_agent(self):
        """
        repairAgentRouting.branch-drift-guard-has-repair: branch-drift-guard/SKILL.md
        must mention repair-agent as one of the worker agents it applies to.

        If this test fails: the skill does not document that the guard applies after repair-agent
        returns, which may cause the guard to be omitted for repair routes.
        # Plan path: repairAgentRouting.branch-drift-guard-has-repair
        """
        content = _full(BRANCH_DRIFT_GUARD_SKILL_PATH)
        assert "repair-agent" in content, (
            "branch-drift-guard/SKILL.md must include repair-agent in the list of worker agents "
            "the guard applies to. Without this, the guard may be skipped for repair routes."
        )

    def test_git_c_worktree_skill_uses_repair_agent(self):
        """
        repairAgentRouting.git-c-worktree-name: git-c-worktree-subagent/SKILL.md must reference
        repair-agent (not repair-implementation-agent) in its list of sub-agents.

        If this test fails: the skill doc names a non-existent agent. An LLM following this
        skill to review agent git usage would look for a non-existent file.
        # Plan path: repairAgentRouting.git-c-worktree-name
        """
        content = _full(GIT_C_WORKTREE_SKILL_PATH)
        assert "repair-implementation-agent" not in content, (
            "git-c-worktree-subagent/SKILL.md must NOT reference repair-implementation-agent. "
            "The agent was renamed to repair-agent. Update the sub-agent list to use repair-agent."
        )

    def test_git_c_worktree_skill_mentions_repair_agent(self):
        """
        repairAgentRouting.git-c-worktree-has-repair: git-c-worktree-subagent/SKILL.md
        must mention repair-agent as one of the sub-agents covered by the git -C rule.

        If this test fails: repair-agent is not covered by the git worktree isolation guidance,
        making it prone to committing to the wrong branch.
        # Plan path: repairAgentRouting.git-c-worktree-has-repair
        """
        content = _full(GIT_C_WORKTREE_SKILL_PATH)
        assert "repair-agent" in content, (
            "git-c-worktree-subagent/SKILL.md must include repair-agent in the list of sub-agents "
            "that must use git -C WORK_DIR. Without this, repair-agent may commit to the wrong branch."
        )
