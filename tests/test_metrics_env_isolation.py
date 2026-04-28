"""
Reproduction test for bug: metrics.csv never written.

Root cause: export DARK_FACTORY_WORK_DIR=<WORK_DIR> inside an LLM Bash tool call
creates the env var only in that subprocess. When Claude Code fires hook subprocesses,
they inherit Claude Code's own environment, NOT any Bash tool call's environment.
So DARK_FACTORY_WORK_DIR is always unset in hooks, causing the no-brain path to fire
and metrics to never accumulate.

These tests reproduce the failure and verify the fix:
- write a pointer file at /tmp/dark-factory-work-dir
- hooks fall back to reading that file when DARK_FACTORY_WORK_DIR is unset
- dark-factory-agent cleanup removes the pointer file
"""

import json
import os
import subprocess
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_HOOK = os.path.join(REPO_ROOT, "agents", "dark-factory", "scripts", "pre-tool-use-hook.sh")
POST_HOOK = os.path.join(REPO_ROOT, "agents", "dark-factory", "scripts", "post-tool-use-hook.sh")

POINTER_FILE = "/tmp/dark-factory-work-dir"


def make_brain(tmpdir, metrics=None):
    brain = {
        "taskDescription": "test task",
        "taskName": "test",
        "workDir": tmpdir,
        "projectDir": "/tmp/project",
        "classification": "feature",
        "planFilePath": None,
        "bugFiles": None,
        "prUrl": None,
        "docsWritten": None,
        "skillsWritten": None,
        "phases": {
            "prep-running": False,
            "prep-complete": True,
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
        },
    }
    if metrics is not None:
        brain["metrics"] = metrics
    return brain


def run_hook(hook_path, stdin_payload, env_override=None):
    """Run a hook script with the given stdin and env overrides."""
    env = dict(os.environ)
    # Remove any pre-existing DARK_FACTORY_WORK_DIR from the real environment
    env.pop("DARK_FACTORY_WORK_DIR", None)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", hook_path],
        input=json.dumps(stdin_payload),
        capture_output=True,
        text=True,
        env=env,
    )


class TestMetricsEnvIsolationBug:
    """
    Regression tests for the metrics env isolation bug.

    These tests verify that hooks work correctly even when DARK_FACTORY_WORK_DIR
    is not set in the hook process's environment (the original bug) — by reading
    the pointer file at /tmp/dark-factory-work-dir as a fallback.
    """

    def test_pre_hook_no_env_var_is_noop_without_pointer_file(self):
        """
        REGRESSION: When DARK_FACTORY_WORK_DIR is unset AND pointer file absent,
        pre-hook must pass stdin through unchanged (no-brain path).

        This was always true — both before and after the fix. The fix adds a
        *new* path where the pointer file IS present. This test confirms the
        no-brain path still works when neither env var nor pointer file exists.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(tmpdir)
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            # Ensure no pointer file exists
            if os.path.exists(POINTER_FILE):
                os.remove(POINTER_FILE)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "planning-agent", "prompt": "do work"},
            }

            # No DARK_FACTORY_WORK_DIR, no pointer file
            result = run_hook(PRE_HOOK, hook_input)

            assert result.returncode == 0
            # No metrics written — the hook exited early on no-brain path
            with open(brain_path) as f:
                updated = json.load(f)
            assert "metrics" not in updated

    def test_post_hook_no_env_var_is_noop_without_pointer_file(self):
        """
        REGRESSION: When DARK_FACTORY_WORK_DIR is unset AND pointer file absent,
        post-hook must exit 0 without accumulating metrics.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(tmpdir)
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            # Ensure no pointer file exists
            if os.path.exists(POINTER_FILE):
                os.remove(POINTER_FILE)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {"subagent_type": "planning-agent", "prompt": "x"},
                "tool_response": {"usage": {"input_tokens": 100, "output_tokens": 50}},
            }

            result = run_hook(POST_HOOK, hook_input)

            assert result.returncode == 0
            with open(brain_path) as f:
                updated = json.load(f)
            assert "metrics" not in updated

    def test_pre_hook_uses_pointer_file_when_env_var_unset(self):
        """
        FIX VERIFICATION: When DARK_FACTORY_WORK_DIR is unset but pointer file
        exists pointing to a valid brain.json directory, pre-hook must write
        start_ms into brain.json metrics.

        This is the fix for the env isolation bug.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(tmpdir)
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            # Write pointer file pointing to tmpdir (no trailing slash)
            with open(POINTER_FILE, "w") as f:
                f.write(tmpdir)

            try:
                hook_input = {
                    "tool_name": "Agent",
                    "tool_input": {
                        "subagent_type": "planning-agent",
                        "prompt": "do work",
                    },
                }

                # DARK_FACTORY_WORK_DIR is unset — hook must use pointer file
                result = run_hook(PRE_HOOK, hook_input)

                assert result.returncode == 0, f"stderr: {result.stderr}"
                with open(brain_path) as f:
                    updated = json.load(f)

                assert "metrics" in updated, (
                    "Metrics key missing — hook did not use pointer file fallback"
                )
                assert "planning-agent" in updated["metrics"], (
                    "planning-agent key missing in metrics"
                )
                assert "start_ms" in updated["metrics"]["planning-agent"], (
                    "start_ms not written — hook still hit no-brain path"
                )
            finally:
                if os.path.exists(POINTER_FILE):
                    os.remove(POINTER_FILE)

    def test_post_hook_uses_pointer_file_when_env_var_unset(self):
        """
        FIX VERIFICATION: When DARK_FACTORY_WORK_DIR is unset but pointer file
        exists, post-hook must accumulate elapsed_ms, tokens, and runs.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(
                tmpdir,
                metrics={"planning-agent": {"start_ms": 1000000000000, "elapsed_ms": 0, "tokens": 0, "runs": 0}},
            )
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            # Write pointer file
            with open(POINTER_FILE, "w") as f:
                f.write(tmpdir)

            try:
                hook_input = {
                    "tool_name": "Agent",
                    "tool_input": {"subagent_type": "planning-agent", "prompt": "x"},
                    "tool_response": {"usage": {"input_tokens": 100, "output_tokens": 50}},
                }

                result = run_hook(POST_HOOK, hook_input)

                assert result.returncode == 0, f"stderr: {result.stderr}"
                with open(brain_path) as f:
                    updated = json.load(f)

                m = updated.get("metrics", {}).get("planning-agent", {})
                assert m.get("runs") == 1, (
                    f"runs={m.get('runs')} — post-hook did not accumulate via pointer file"
                )
                assert m.get("tokens") == 150, (
                    f"tokens={m.get('tokens')} — expected 150"
                )
                assert "start_ms" not in m, "start_ms should be deleted after accumulation"
            finally:
                if os.path.exists(POINTER_FILE):
                    os.remove(POINTER_FILE)

    def test_env_var_takes_precedence_over_pointer_file(self):
        """
        When DARK_FACTORY_WORK_DIR is set AND pointer file exists pointing to a
        different dir, the env var must win (env var takes precedence).
        """
        with tempfile.TemporaryDirectory() as env_dir:
            with tempfile.TemporaryDirectory() as pointer_dir:
                # Write brain.json in the env_dir only
                brain = make_brain(env_dir)
                brain_path = os.path.join(env_dir, "brain.json")
                with open(brain_path, "w") as f:
                    json.dump(brain, f)

                # Pointer file points to pointer_dir (no brain.json there)
                with open(POINTER_FILE, "w") as f:
                    f.write(pointer_dir)

                try:
                    hook_input = {
                        "tool_name": "Agent",
                        "tool_input": {
                            "subagent_type": "planning-agent",
                            "prompt": "do work",
                        },
                    }

                    # Set env var to env_dir — should use env_dir's brain.json
                    result = run_hook(
                        PRE_HOOK,
                        hook_input,
                        env_override={"DARK_FACTORY_WORK_DIR": env_dir},
                    )

                    assert result.returncode == 0, f"stderr: {result.stderr}"
                    with open(brain_path) as f:
                        updated = json.load(f)

                    # Brain in env_dir must have been updated (env var took precedence)
                    assert "metrics" in updated, "env_dir brain.json should have been updated"
                    assert "planning-agent" in updated["metrics"]
                finally:
                    if os.path.exists(POINTER_FILE):
                        os.remove(POINTER_FILE)
