"""
Tests for phase-order-enforcement-hook.sh

Verifies that:
- Phase order is allowed when all prerequisite phases are complete.
- Phase order is blocked (SubagentStop raised) when earlier phases are incomplete.
- Marking a phase complete updates brain.json correctly.

Flow: check-phase-order, mark-phase-complete
"""

import json
import os
import subprocess
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASE_HOOK = os.path.join(
    REPO_ROOT,
    "agents",
    "dark-factory",
    "scripts",
    "phase-order-enforcement-hook.sh",
)


def make_brain(completed_phases=None):
    """Build a minimal brain.json with an optional completed_phases list."""
    # TODO (check-phase-order): Extend with any additional brain fields required
    #   by the hook implementation.
    return {
        "taskDescription": "test task",
        "taskName": "test",
        "workDir": "/tmp/test",
        "projectDir": "/tmp/project",
        "phases": {
            "completedPhases": completed_phases or [],
        },
    }


def run_hook(tool_input: dict, env_override: dict | None = None) -> subprocess.CompletedProcess:
    """Run phase-order-enforcement-hook.sh with given tool_input JSON via stdin."""
    # TODO (check-phase-order): no additional setup needed — stub only.
    env = dict(os.environ)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", PHASE_HOOK],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
    )


class TestCheckPhaseOrderAllowed:
    """Flow: check-phase-order — allowed path"""

    def test_unknown_agent_allowed(self):
        """
        check-phase-order.allowed: agents not in the phase map are always allowed.
        # Plan path: check-phase-order.allowed
        # TODO (check-phase-order): implement
        """
        raise NotImplementedError("TODO (check-phase-order): implement test")

    def test_first_phase_always_allowed(self):
        """
        check-phase-order.allowed: phase 1 is always allowed regardless of state.
        # Plan path: check-phase-order.allowed
        # TODO (check-phase-order): implement
        """
        raise NotImplementedError("TODO (check-phase-order): implement test")

    def test_phase_allowed_when_prerequisites_complete(self):
        """
        check-phase-order.allowed: phase N allowed when phases 1..N-1 are complete.
        # Plan path: check-phase-order.allowed
        # TODO (check-phase-order): implement
        """
        raise NotImplementedError("TODO (check-phase-order): implement test")


class TestCheckPhaseOrderBlocked:
    """Flow: check-phase-order — blocked / error path"""

    def test_phase_blocked_when_prerequisites_incomplete(self):
        """
        check-phase-order.blocked: SubagentStop raised when earlier phases are incomplete.
        # Plan path: check-phase-order.blocked
        # TODO (check-phase-order): implement
        """
        raise NotImplementedError("TODO (check-phase-order): implement test")

    def test_blocked_message_lists_incomplete_phases(self):
        """
        check-phase-order.blocked: error message names the specific incomplete phases.
        # Plan path: check-phase-order.blocked
        # TODO (check-phase-order): implement
        """
        raise NotImplementedError("TODO (check-phase-order): implement test")


class TestMarkPhaseComplete:
    """Flow: mark-phase-complete"""

    def test_mark_phase_updates_brain(self):
        """
        mark-phase-complete.success: phaseNumber appended to completedPhases in brain.json.
        # Plan path: mark-phase-complete.success
        # TODO (mark-phase-complete): implement
        """
        raise NotImplementedError("TODO (mark-phase-complete): implement test")

    def test_mark_phase_error_on_unwritable_brain(self):
        """
        mark-phase-complete.error: returns error when brain.json is not writable.
        # Plan path: mark-phase-complete.error
        # TODO (mark-phase-complete): implement
        """
        raise NotImplementedError("TODO (mark-phase-complete): implement test")
