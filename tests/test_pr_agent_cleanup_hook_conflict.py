"""
Regression test for: pr-agent SubagentStop hook destroys worktree before
dark-factory-agent can finish Steps 11-12.

Bug: pr-agent.md declares SubagentStop: pr-agent-cleanup-hook.sh.
When pr-agent stops, this hook fires and destroys the git worktree (including
brain.json). dark-factory-agent Steps 11-12 then fail because brain.json is
gone before the orchestrator reads prUrl/projectDir and flushes metrics.

Fix: Remove the SubagentStop hook from pr-agent.md. dark-factory-agent owns
the cleanup lifecycle in Step 12.

See: docs/bugs/2026-05-08-pr-agent-cleanup-hook-destroys-worktree-early.md

Flow: prAgentCleanupHookConflict
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PR_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "pr", "agents", "pr-agent.md"
)
DARK_FACTORY_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "dark-factory", "agents", "dark-factory-agent.md"
)


def _frontmatter(path: str) -> str:
    """Return only the YAML frontmatter block of a file."""
    with open(path) as f:
        content = f.read()
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    return match.group(1) if match else ""


def _body(path: str) -> str:
    """Return the body of a file (everything after the closing front-matter ---)."""
    with open(path) as f:
        content = f.read()
    fm_end = content.find("\n---", 4)
    return content[fm_end + 4:] if fm_end != -1 else content


class TestPrAgentSubagentStopConflict:
    """
    prAgentCleanupHookConflict — pr-agent must NOT declare a SubagentStop hook
    that destroys the worktree. dark-factory-agent owns cleanup (Step 12).

    Root cause: When pr-agent's SubagentStop hook fires, it calls
    cleanup-worktree.sh which removes the worktree (including brain.json).
    dark-factory-agent Steps 11-12 need the worktree to exist after pr-agent
    returns to read prUrl/projectDir and flush metrics.

    The SubagentStop fires BEFORE the Agent tool call returns to
    dark-factory-agent. So when dark-factory-agent continues to Step 11, the
    worktree is already gone.
    """

    def test_pr_agent_has_no_subagent_stop_cleanup_hook(self):
        """
        prAgentCleanupHookConflict.no-subagent-stop: pr-agent.md must NOT declare
        a SubagentStop hook that calls cleanup-worktree.sh or pr-agent-cleanup-hook.sh.

        If this test fails: pr-agent.md still has a SubagentStop hook that destroys
        the worktree prematurely. dark-factory-agent Steps 11-12 will fail because
        brain.json is gone when the orchestrator tries to read it.

        Fix: Remove the SubagentStop declaration from pr-agent.md YAML frontmatter.
        dark-factory-agent already owns cleanup in Step 12.
        # Plan path: prAgentCleanupHookConflict.no-subagent-stop
        """
        frontmatter = _frontmatter(PR_AGENT_PATH)
        assert "SubagentStop" not in frontmatter, (
            "pr-agent.md must NOT declare a SubagentStop hook. "
            "The SubagentStop hook fires when pr-agent stops, BEFORE dark-factory-agent "
            "regains control after Step 10. dark-factory-agent Steps 11-12 need brain.json "
            "from the worktree (to read prUrl/projectDir and flush metrics). "
            "Remove the SubagentStop from pr-agent.md — dark-factory-agent handles cleanup "
            "in Step 12 by calling cleanup-worktree.sh explicitly."
        )

    def test_pr_agent_subagent_stop_does_not_reference_cleanup_worktree(self):
        """
        prAgentCleanupHookConflict.no-cleanup-worktree-ref: pr-agent.md must NOT
        reference cleanup-worktree.sh in a SubagentStop context.

        If this test fails: pr-agent's SubagentStop hook eventually calls
        cleanup-worktree.sh. This destroys the worktree before dark-factory-agent
        can complete its Steps 11-12.
        # Plan path: prAgentCleanupHookConflict.no-cleanup-worktree-ref
        """
        frontmatter = _frontmatter(PR_AGENT_PATH)
        # Check that no SubagentStop line in frontmatter references the cleanup hook
        for line in frontmatter.splitlines():
            if "SubagentStop" in line:
                assert "cleanup" not in line.lower(), (
                    f"pr-agent.md SubagentStop hook must NOT reference cleanup scripts. "
                    f"Found: {line.strip()}\n"
                    "A cleanup SubagentStop destroys the worktree before dark-factory-agent "
                    "can read brain.json for prUrl/projectDir in Step 11."
                )

    def test_dark_factory_agent_owns_cleanup_in_step_12(self):
        """
        prAgentCleanupHookConflict.dfa-owns-cleanup: dark-factory-agent.md must contain
        cleanup-worktree.sh invocation in Step 12 (after pr-agent returns).

        This verifies that dark-factory-agent is the sole owner of cleanup. If pr-agent
        also runs cleanup via SubagentStop, there is a double-cleanup conflict.
        # Plan path: prAgentCleanupHookConflict.dfa-owns-cleanup
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        assert "cleanup-worktree.sh" in body, (
            "dark-factory-agent.md must contain a cleanup-worktree.sh invocation in Step 12. "
            "dark-factory-agent is the orchestrator and owns the full lifecycle including cleanup. "
            "If this invocation is missing, the worktree may never be removed after manufacture."
        )

    def test_pr_agent_cleanup_hook_script_exists_but_is_not_auto_triggered(self):
        """
        prAgentCleanupHookConflict.hook-script-exists: pr-agent-cleanup-hook.sh script
        can exist in the scripts directory, but it must not be declared in pr-agent.md
        as a SubagentStop.

        The script is preserved for potential future use or standalone pr-agent scenarios,
        but within the manufacture flow it must not auto-trigger.
        # Plan path: prAgentCleanupHookConflict.hook-script-exists
        """
        cleanup_hook_path = os.path.join(
            PROJECT_ROOT, "agents", "dark-factory", "scripts", "pr-agent-cleanup-hook.sh"
        )
        # Script may or may not exist — this test just verifies the SubagentStop
        # is not in pr-agent.md regardless of whether the script file exists.
        # (The script can exist; it just shouldn't be auto-triggered on pr-agent stop.)
        frontmatter = _frontmatter(PR_AGENT_PATH)
        assert "pr-agent-cleanup-hook" not in frontmatter, (
            "pr-agent.md must NOT reference pr-agent-cleanup-hook.sh in YAML frontmatter. "
            "This hook, when wired as SubagentStop, destroys the worktree before "
            "dark-factory-agent Steps 11-12 can complete. "
            "Remove the SubagentStop line from pr-agent.md frontmatter."
        )
