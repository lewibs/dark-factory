"""
Regression tests for: feature-agent commits to main branch instead of feature worktree branch.

Two root causes are verified:

1. Branch-drift guard: dark-factory-agent.md must contain a guard after the worker
   returns (Step 3) that verifies feature/<taskName> has commits not on main. If the
   worker committed to the wrong branch (or not at all), the orchestrator must halt
   with a clear error rather than silently proceeding to code review with empty changes.

2. create-pr must NOT create a new branch: The create-pr skill must not run
   `git checkout -b fix/<slug>` because the worktree is already on the correct
   feature/<taskName> branch. Creating a new branch off the main worktree CWD causes
   commits to land on main (or on a fix/ branch branched from main, not feature/).

3. pr-agent must use WORK_DIR for git operations: pr-agent's git commands must
   reference WORK_DIR (via `git -C "$WORK_DIR"` or by running from WORK_DIR) so they
   operate on the feature worktree, not the main worktree.

See: docs/bugs/2026-04-29-feature-agent-commits-to-main.md
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DARK_FACTORY_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "dark-factory", "agents", "dark-factory-agent.md"
)
CREATE_PR_SKILL_PATH = os.path.join(
    PROJECT_ROOT, "skills", "create-pr", "SKILL.md"
)
PR_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "pr", "agents", "pr-agent.md"
)


def _body(path: str) -> str:
    """Return the body of an agent/skill file (everything after the closing front-matter ---)."""
    with open(path) as f:
        content = f.read()
    fm_end = content.find("\n---", 4)
    return content[fm_end + 4:] if fm_end != -1 else content


def _full(path: str) -> str:
    """Return the full file content."""
    with open(path) as f:
        return f.read()


class TestBranchDriftGuard:
    """Flow: branchDriftGuard — dark-factory-agent must verify feature branch is ahead of main after worker."""

    def test_dark_factory_agent_has_branch_drift_guard(self):
        """
        branchDriftGuard.guard-present: dark-factory-agent.md must contain a branch-drift
        guard after the worker agent returns (Step 3) and before proceeding to Step 4.

        The guard must check that feature/<taskName> has commits that main does not. If the
        worker committed to the wrong branch, this guard halts with a clear error.

        If this test fails: the branch-drift guard has been removed or never added, meaning
        a worker that commits to main will silently proceed through code review with no changes.
        # Plan path: branchDriftGuard.guard-present
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Guard should reference checking that feature branch is ahead of main
        assert re.search(
            r"(?i)(branch.drift|drift.guard|ahead.of.main|log.*main\.\.|\.\.HEAD|feature.*commits|commits.*feature|worker.*commit|commit.*wrong|feature.*ahead)",
            body,
        ), (
            "dark-factory-agent.md must contain a branch-drift guard after the worker returns "
            "(Step 3) that verifies feature/<taskName> has commits not on main. "
            "Without this guard, a worker that commits to the wrong branch proceeds silently "
            "through code review with no changes."
        )

    def test_dark_factory_agent_branch_drift_guard_is_after_worker(self):
        """
        branchDriftGuard.guard-position: the branch-drift guard must appear after Step 4
        (worker invocation) and before Step 7 (code review) in dark-factory-agent.md.

        Step numbering: Step 4 = route to worker agent, Step 5 = branch-drift guard,
        Step 6 = read planFilePath, Step 7 = code review. The guard must be after the
        worker commits (Step 4) and before code review (Step 7).

        If this test fails: the guard exists but is in the wrong position — it may run before
        the worker has committed (making it ineffective) or after code review (too late).
        # Plan path: branchDriftGuard.guard-position
        """
        body = _body(DARK_FACTORY_AGENT_PATH)

        # Find positions of Step 4 (worker), the guard, and Step 7 (code review).
        # Use line-start anchors (via re.MULTILINE) to match the actual section headers,
        # not inline references like "# proceed to Step 7 (code review)".
        step4_match = re.search(r"(?im)^\s*#\s*Step\s+4\b", body)
        step7_match = re.search(r"(?im)^\s*#\s*Step\s+7\b", body)

        assert step4_match, "dark-factory-agent.md must contain a '# Step 4' section header (worker invocation)"
        assert step7_match, "dark-factory-agent.md must contain a '# Step 7' section header (code review)"

        guard_match = re.search(
            r"(?i)(branch.drift|drift.guard|log.*main\.\.|feature.*ahead|commits.*feature|worker.*commit.*wrong)",
            body,
        )
        assert guard_match, (
            "dark-factory-agent.md must contain a branch-drift guard expression"
        )

        step4_pos = step4_match.start()
        step7_pos = step7_match.start()
        guard_pos = guard_match.start()

        assert step4_pos < guard_pos < step7_pos, (
            f"Branch-drift guard (pos {guard_pos}) must appear after Step 4 worker (pos {step4_pos}) "
            f"and before Step 7 code-review (pos {step7_pos}) in dark-factory-agent.md. "
            f"The guard must run after the worker commits and before code review begins."
        )

    def test_dark_factory_agent_branch_drift_halt_on_empty(self):
        """
        branchDriftGuard.halt-message: dark-factory-agent.md must halt with a clear error
        message when the feature branch has no commits ahead of main.

        If this test fails: the guard detects the drift condition but does not halt — meaning
        dark-factory-agent silently proceeds to code review with no changes.
        # Plan path: branchDriftGuard.halt-message
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Must mention halting / error when no commits found
        assert re.search(
            r"(?i)(halt|stop|error|fail).{0,100}(no commit|wrong branch|main|commit.*missing|worker.*commit)",
            body,
        ) or re.search(
            r"(?i)(no commit|wrong branch|commit.*missing).{0,100}(halt|stop|error|fail)",
            body,
        ), (
            "dark-factory-agent.md must halt with an error when the branch-drift guard finds "
            "no commits on feature/<taskName> ahead of main. The error message should indicate "
            "the worker may have committed to the wrong branch."
        )


class TestCreatePrNoBranchSwitch:
    """Flow: createPrNoBranchSwitch — create-pr skill must NOT create a new branch."""

    def test_create_pr_does_not_checkout_new_branch(self):
        """
        createPrNoBranchSwitch.no-checkout-b: create-pr/SKILL.md must NOT contain
        `git checkout -b` because the worktree is already on feature/<taskName>.

        Running `git checkout -b fix/<slug>` from the main worktree CWD creates a new
        branch off main, and the subsequent commit lands there instead of feature/<taskName>.

        If this test fails: create-pr is still creating a new branch, which is the root
        cause of commits landing on main.
        # Plan path: createPrNoBranchSwitch.no-checkout-b
        """
        content = _full(CREATE_PR_SKILL_PATH)
        assert "git checkout -b" not in content, (
            "create-pr/SKILL.md must NOT contain `git checkout -b`. "
            "The worktree is already on the correct feature/<taskName> branch. "
            "Creating a new branch from the main worktree CWD causes commits to land on main. "
            "Remove the `git checkout -b fix/<slug>` step entirely."
        )

    def test_create_pr_uses_existing_branch(self):
        """
        createPrNoBranchSwitch.use-existing-branch: create-pr/SKILL.md must document that
        it commits to the existing feature branch (not create a new one).

        The PR push should use `git push -u origin HEAD` from WORK_DIR so it pushes
        feature/<taskName>, not a newly-created fix/ branch off main.

        If this test fails: create-pr has no instruction about working on the existing
        feature branch, leaving it ambiguous and prone to re-introducing the bug.
        # Plan path: createPrNoBranchSwitch.use-existing-branch
        """
        content = _full(CREATE_PR_SKILL_PATH)
        # Must mention working on the current branch / feature branch
        assert re.search(
            r"(?i)(current branch|feature.*branch|existing branch|WORK_DIR|worktree|feature/<)",
            content,
        ), (
            "create-pr/SKILL.md must explicitly state that it commits to the existing "
            "feature branch (the worktree branch), not create a new one. "
            "This prevents future regressions of the checkout-b pattern."
        )


class TestPrAgentUsesWorkDir:
    """Flow: prAgentUsesWorkDir — pr-agent must use WORK_DIR for git operations."""

    def test_pr_agent_references_work_dir_for_git(self):
        """
        prAgentUsesWorkDir.work-dir-git: pr-agent.md must reference WORK_DIR for git
        operations so that commits go to the feature worktree, not the main worktree.

        If this test fails: pr-agent has no WORK_DIR awareness and will run git commands
        from whatever CWD the Claude Code process started in (the main worktree).
        # Plan path: prAgentUsesWorkDir.work-dir-git
        """
        body = _body(PR_AGENT_PATH)
        assert re.search(
            r"(?i)(WORK_DIR|work_dir|worktree|git -C|cd.*WORK)",
            body,
        ), (
            "pr-agent.md must reference WORK_DIR (or instruct running git with -C $WORK_DIR) "
            "for all git operations. Without this, git commands run from the main worktree CWD "
            "and commits land on main instead of feature/<taskName>."
        )
