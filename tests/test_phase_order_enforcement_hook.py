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
import stat
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
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(completed_phases=[])
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "agentName": "unknown-agent-xyz",
                    "currentPhase": 3,
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            assert out.get("allowed") is True, (
                f"Expected allowed=true for unknown agent, got: {out}"
            )

    def test_first_phase_always_allowed(self):
        """
        check-phase-order.allowed: phase 1 is always allowed regardless of state.
        # Plan path: check-phase-order.allowed
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(completed_phases=[])
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "agentName": "dark-factory-agent",
                    "currentPhase": 1,
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            assert out.get("allowed") is True, (
                f"Expected allowed=true for phase 1 with no prerequisites, got: {out}"
            )

    def test_phase_allowed_when_prerequisites_complete(self):
        """
        check-phase-order.allowed: phase N allowed when phases 1..N-1 are complete.
        # Plan path: check-phase-order.allowed
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(completed_phases=[1, 2])
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "agentName": "dark-factory-agent",
                    "currentPhase": 3,
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            assert out.get("allowed") is True, (
                f"Expected allowed=true when phases 1 and 2 are complete, got: {out}"
            )


class TestCheckPhaseOrderBlocked:
    """Flow: check-phase-order — blocked / error path"""

    def test_phase_blocked_when_prerequisites_incomplete(self):
        """
        check-phase-order.blocked: SubagentStop raised when earlier phases are incomplete.
        # Plan path: check-phase-order.blocked
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Phase 1 not completed, trying to run phase 2
            brain = make_brain(completed_phases=[])
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "agentName": "dark-factory-agent",
                    "currentPhase": 2,
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            # Hook should output allowed=false and a non-zero exit (SubagentStop) or
            # return a JSON with allowed=false and a reason
            out = json.loads(result.stdout)
            assert out.get("allowed") is False, (
                f"Expected allowed=false when phase 1 incomplete and attempting phase 2, got: {out}"
            )
            assert out.get("reason") is not None, (
                f"Expected a reason field when blocked, got: {out}"
            )

    def test_blocked_message_lists_incomplete_phases(self):
        """
        check-phase-order.blocked: error message names the specific incomplete phases.
        # Plan path: check-phase-order.blocked
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only phase 1 complete, skipped phase 2, trying to run phase 3
            brain = make_brain(completed_phases=[1])
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "agentName": "dark-factory-agent",
                    "currentPhase": 3,
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            out = json.loads(result.stdout)
            assert out.get("allowed") is False, (
                f"Expected allowed=false when phase 2 is incomplete, got: {out}"
            )
            reason = out.get("reason", "")
            assert "2" in reason, (
                f"Expected incomplete phase 2 to be mentioned in reason, got reason: {reason!r}"
            )


class TestMarkPhaseComplete:
    """Flow: mark-phase-complete"""

    def test_mark_phase_updates_brain(self):
        """
        mark-phase-complete.success: phaseNumber appended to completedPhases in brain.json.
        # Plan path: mark-phase-complete.success
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(completed_phases=[])
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "mark-phase-complete",
                    "agentName": "dark-factory-agent",
                    "phaseNumber": 1,
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            assert out.get("updated") is True, (
                f"Expected updated=true after marking phase complete, got: {out}"
            )
            assert 1 in out.get("newCompletedPhases", []), (
                f"Expected phase 1 in newCompletedPhases, got: {out}"
            )

            # Also verify brain.json was actually updated on disk
            with open(brain_path) as f:
                updated_brain = json.load(f)
            assert 1 in updated_brain["phases"]["completedPhases"], (
                f"Expected phase 1 in brain.json completedPhases, got: {updated_brain}"
            )

    def test_mark_phase_error_on_unwritable_brain(self):
        """
        mark-phase-complete.error: returns error when brain.json is not writable.
        # Plan path: mark-phase-complete.error
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(completed_phases=[])
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            # Make brain.json read-only so write will fail
            os.chmod(brain_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            hook_input = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "mark-phase-complete",
                    "agentName": "dark-factory-agent",
                    "phaseNumber": 1,
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            out = json.loads(result.stdout)
            assert out.get("updated") is False, (
                f"Expected updated=false when brain.json is not writable, got: {out}"
            )
            assert out.get("error") is not None, (
                f"Expected an error field when write fails, got: {out}"
            )

            # Restore permissions for cleanup
            os.chmod(brain_path, stat.S_IRUSR | stat.S_IWUSR)
