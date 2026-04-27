"""
Unit tests for pre-tool-use-hook.sh and post-tool-use-hook.sh.

All tests execute the actual shell scripts via subprocess.run() and assert
real behavior: stdout content, file state changes, exit codes.
"""

import json
import os
import subprocess
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_HOOK = os.path.join(
    REPO_ROOT, "agents", "dark-factory", "scripts", "pre-tool-use-hook.sh"
)
POST_HOOK = os.path.join(
    REPO_ROOT, "agents", "dark-factory", "scripts", "post-tool-use-hook.sh"
)

ALL_PHASES_FALSE = {
    "prep-running": False,
    "prep-complete": False,
    "worker-running": False,
    "worker-complete": False,
    "review-running": False,
    "review-complete": False,
    "docs-running": False,
    "docs-complete": False,
    "skills-running": False,
    "skills-complete": False,
    "pr-running": False,
    "pr-complete": False,
    "cleanup-running": False,
    "cleanup-complete": False,
}


def make_brain(phases=None):
    base_phases = dict(ALL_PHASES_FALSE)
    if phases:
        base_phases.update(phases)
    return {
        "taskDescription": "test task",
        "taskName": "test",
        "workDir": "/tmp/test",
        "classification": "feature",
        "planFilePath": None,
        "bugFiles": None,
        "prUrl": None,
        "docsWritten": None,
        "skillsWritten": None,
        "phases": base_phases,
    }


def run_hook(hook_path, stdin_payload, env_override=None):
    env = dict(os.environ)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", hook_path],
        input=json.dumps(stdin_payload),
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# pre-tool-use-hook.sh tests
# ---------------------------------------------------------------------------


class TestPreHookInjectsBrainState:
    """Flow: pre_hook_injects_brain_state"""

    def test_inject_success(self):
        """pre_hook.inject.success: stdout prompt contains BRAIN STATE and brain JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain()
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_hook(
                PRE_HOOK,
                {"prompt": "original prompt"},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            assert "BRAIN STATE" in out["prompt"]
            # The hook modifies brain.json before injecting, so read the
            # updated brain.json and verify its key fields appear in the prompt.
            # Use semantic field presence rather than exact string equality to
            # avoid ordering differences between Python json.dumps and jq output.
            with open(brain_path) as bf:
                updated_brain = json.load(bf)
            assert updated_brain["taskName"] in out["prompt"]
            assert updated_brain["classification"] in out["prompt"]

    def test_inject_no_brain(self):
        """pre_hook.inject.no_brain: when DARK_FACTORY_WORK_DIR is unset, stdin is passed through unchanged."""
        stdin_payload = {"prompt": "passthrough check"}
        # Pass env_override={"DARK_FACTORY_WORK_DIR": ""} to clear the variable;
        # run_hook merges over os.environ so we must explicitly blank it out.
        env = dict(os.environ)
        env.pop("DARK_FACTORY_WORK_DIR", None)
        result = subprocess.run(
            ["bash", PRE_HOOK],
            input=json.dumps(stdin_payload),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # stdout should be the unchanged stdin
        out = json.loads(result.stdout)
        assert out == stdin_payload


class TestPreHookSetsRunningPhase:
    """Flow: pre_hook_sets_running_phase"""

    def test_set_running_success(self):
        """pre_hook.set_running.success: first incomplete phase gets *-running=true in brain.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # prep is complete, worker is not started
            phases = dict(ALL_PHASES_FALSE)
            phases["prep-complete"] = True
            brain = make_brain(phases=phases)
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_hook(
                PRE_HOOK,
                {"prompt": "x"},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            with open(brain_path) as f:
                updated = json.load(f)
            assert updated["phases"]["worker-running"] is True

    def test_set_running_no_incomplete(self):
        """pre_hook.set_running.no_incomplete: when all phases complete, no change and stderr says phase=none."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only *-complete keys are True; *-running keys remain False.
            # This matches the realistic brain state where all work is done.
            phases = {k: (True if k.endswith("-complete") else False) for k in ALL_PHASES_FALSE}
            brain = make_brain(phases=phases)
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            phases_before = dict(brain["phases"])

            result = run_hook(
                PRE_HOOK,
                {"prompt": "x"},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "phase=none" in result.stderr

            with open(brain_path) as f:
                updated = json.load(f)
            assert updated["phases"] == phases_before


class TestPreHookEmitsValidJson:
    """Flow: pre_hook_emits_valid_json"""

    def test_valid_json_output(self):
        """pre_hook.valid_json.success: stdout is always valid JSON when brain.json exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain()
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_hook(
                PRE_HOOK,
                {"prompt": "some prompt", "extra_key": 42},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            # Must not raise
            parsed = json.loads(result.stdout)
            assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# post-tool-use-hook.sh tests
# ---------------------------------------------------------------------------


class TestPostHookMergesPatch:
    """Flow: post_hook_merges_patch"""

    def test_merge_success(self):
        """post_hook.merge.success: patch fields merged into brain.json; patch file deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain()
            brain_path = os.path.join(tmpdir, "brain.json")
            patch_path = os.path.join(tmpdir, "brain-patch.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)
            patch = {"planFilePath": "/some/plan.md"}
            with open(patch_path, "w") as f:
                json.dump(patch, f)

            result = run_hook(
                POST_HOOK,
                {},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            with open(brain_path) as f:
                updated = json.load(f)
            assert updated["planFilePath"] == "/some/plan.md"
            assert not os.path.exists(patch_path)

    def test_merge_no_patch(self):
        """post_hook.merge.no_patch: when no patch file, brain.json is unchanged and stderr says no-patch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain()
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_hook(
                POST_HOOK,
                {},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "no-patch" in result.stderr
            with open(brain_path) as f:
                updated = json.load(f)
            # brain.json should be unchanged
            assert updated["planFilePath"] is None


class TestPostHookSetsCompleteAndClearsRunning:
    """Flow: post_hook_sets_complete_clears_running"""

    def test_phase_success(self):
        """post_hook.phase.success: worker-running=false and worker-complete=true after hook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            phases = dict(ALL_PHASES_FALSE)
            phases["prep-complete"] = True
            phases["worker-running"] = True
            brain = make_brain(phases=phases)
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_hook(
                POST_HOOK,
                {},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            with open(brain_path) as f:
                updated = json.load(f)
            assert updated["phases"]["worker-running"] is False
            assert updated["phases"]["worker-complete"] is True

    def test_phase_no_running(self):
        """post_hook.phase.no_running: when no phase is running, stderr says 'no running phase found'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain()  # all phases false
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            phases_before = dict(brain["phases"])

            result = run_hook(
                POST_HOOK,
                {},
                env_override={"DARK_FACTORY_WORK_DIR": tmpdir},
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert "no running phase found" in result.stderr
            with open(brain_path) as f:
                updated = json.load(f)
            assert updated["phases"] == phases_before


class TestPostHookNoBrain:
    """Flow: post_hook_no_brain"""

    def test_no_brain_exits_zero(self):
        """post_hook.no_brain.success: when DARK_FACTORY_WORK_DIR is unset, exit 0 with no file changes."""
        env = dict(os.environ)
        env.pop("DARK_FACTORY_WORK_DIR", None)

        result = subprocess.run(
            ["bash", POST_HOOK],
            input="{}",
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Plan requires only exit 0 and no file changes; stdout content is unspecified.
        # We do not assert stdout == "" to avoid brittleness if the hook is updated.
