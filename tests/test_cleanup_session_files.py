"""
Unit tests for cleanup-session-files.sh.

Tests cover:
- Metrics are flushed to CSV before brain.json is deleted
- Session files are properly cleaned up
- Script handles missing projectDir gracefully
- Script handles missing update-metrics.py gracefully
"""

import csv
import json
import os
import subprocess
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANUP_SCRIPT = os.path.join(
    REPO_ROOT, "agents", "dark-factory", "scripts", "cleanup-session-files.sh"
)
UPDATE_METRICS_SCRIPT = os.path.join(REPO_ROOT, "scripts", "update-metrics.py")


def make_brain(project_dir=None, metrics=None):
    """Create a minimal brain.json dict."""
    brain = {
        "taskDescription": "test task",
        "taskName": "test",
        "workDir": "/tmp/test",
        "projectDir": project_dir,
        "classification": "feature",
        "planFilePath": None,
        "bugFiles": None,
        "prUrl": None,
        "docsWritten": None,
        "skillsWritten": None,
        "phases": {},
    }
    if metrics is not None:
        brain["metrics"] = metrics
    return brain


def run_cleanup(work_dir, env_override=None):
    """Run cleanup-session-files.sh and return CompletedProcess."""
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = REPO_ROOT
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", CLEANUP_SCRIPT],
        capture_output=True,
        text=True,
        env=env,
    )


def read_csv_rows(csv_path):
    """Return list of row dicts from csv_path; empty list if file absent."""
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


class TestCleanupFlushesMetrics:
    """Flow: cleanupFlushesMetrics"""

    def test_success_flushes_metrics_before_delete(self):
        """cleanupFlushesMetrics.success: metrics are flushed to CSV before brain.json is deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: create a work dir with brain.json and a project dir with metrics.csv
            brain = make_brain(
                project_dir=tmpdir,
                metrics={
                    "feature-agent": {
                        "elapsed_ms": 1000,
                        "tokens": 200,
                        "runs": 1,
                    }
                },
            )
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            csv_path = os.path.join(tmpdir, "metrics.csv")

            # Run cleanup
            result = run_cleanup(tmpdir, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"

            # Verify metrics were flushed to CSV
            assert os.path.exists(csv_path), "metrics.csv should exist after cleanup"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 1
            assert rows[0]["agent"] == "feature-agent"
            assert int(rows[0]["runs"]) == 1

            # Verify brain.json was deleted
            assert not os.path.exists(brain_path), "brain.json should be deleted after cleanup"

    def test_flush_no_metrics(self):
        """cleanupFlushesMetrics.no-metrics: cleanup creates empty CSV even when brain.json has no metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(project_dir=tmpdir, metrics={})
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            csv_path = os.path.join(tmpdir, "metrics.csv")

            result = run_cleanup(tmpdir, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            # CSV should be created even with no metrics (for consistency)
            assert os.path.exists(csv_path), "CSV should be created even when there are no metrics"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 0, "CSV should have no data rows when metrics are empty"
            assert not os.path.exists(brain_path), "brain.json should be deleted"

    def test_flush_no_project_dir(self):
        """cleanupFlushesMetrics.no-project-dir: cleanup succeeds when projectDir is null."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(
                project_dir=None,
                metrics={
                    "feature-agent": {"elapsed_ms": 1000, "tokens": 200, "runs": 1}
                },
            )
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_cleanup(tmpdir, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            # brain.json should be deleted even if projectDir is null
            assert not os.path.exists(brain_path)

    def test_flush_missing_update_metrics_script(self):
        """cleanupFlushesMetrics.missing-script: cleanup succeeds even if update-metrics.py is not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(
                project_dir=tmpdir,
                metrics={
                    "feature-agent": {"elapsed_ms": 1000, "tokens": 200, "runs": 1}
                },
            )
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            # Clear CLAUDE_PLUGIN_ROOT so script can't find update-metrics.py
            result = run_cleanup(
                tmpdir,
                env_override={
                    "DARK_FACTORY_WORK_DIR": tmpdir,
                    "CLAUDE_PLUGIN_ROOT": "",
                },
            )

            assert result.returncode == 0, f"stderr: {result.stderr}"
            # brain.json should still be deleted
            assert not os.path.exists(brain_path)

    def test_flush_accumulates_with_existing_csv(self):
        """cleanupFlushesMetrics.accumulate: metrics accumulate with existing CSV rows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")

            # Pre-populate CSV with one row
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "agent",
                        "skill",
                        "avg_runtime",
                        "avg_tokens",
                        "runs",
                        "sum_runtime",
                        "sum_tokens",
                    ],
                )
                writer.writeheader()
                writer.writerow({
                    "agent": "feature-agent",
                    "skill": "",
                    "avg_runtime": "1000.0",
                    "avg_tokens": "200.0",
                    "runs": "1",
                    "sum_runtime": "1000.0",
                    "sum_tokens": "200.0",
                })

            brain = make_brain(
                project_dir=tmpdir,
                metrics={
                    "feature-agent": {"elapsed_ms": 2000, "tokens": 400, "runs": 1}
                },
            )
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_cleanup(tmpdir, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"

            # Verify metrics accumulated
            rows = read_csv_rows(csv_path)
            assert len(rows) == 1
            assert int(rows[0]["runs"]) == 2


class TestCleanupDeletesSessionFiles:
    """Flow: cleanupDeletesSessionFiles"""

    def test_deletes_brain_json(self):
        """cleanupDeletesSessionFiles.brain: brain.json is deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(project_dir=tmpdir)
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            result = run_cleanup(tmpdir, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert not os.path.exists(brain_path)

    def test_deletes_all_session_files(self):
        """cleanupDeletesSessionFiles.all: all session files are deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain(project_dir=tmpdir)
            brain_path = os.path.join(tmpdir, "brain.json")
            patch_path = os.path.join(tmpdir, "brain-patch.json")
            flows_path = os.path.join(tmpdir, "flows-state.json")
            lock_path = os.path.join(tmpdir, "brain.json.lock")

            with open(brain_path, "w") as f:
                json.dump(brain, f)
            with open(patch_path, "w") as f:
                json.dump({}, f)
            with open(flows_path, "w") as f:
                json.dump({}, f)
            with open(lock_path, "w") as f:
                f.write("")

            result = run_cleanup(tmpdir, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert not os.path.exists(brain_path)
            assert not os.path.exists(patch_path)
            assert not os.path.exists(flows_path)
            assert not os.path.exists(lock_path)

    def test_no_work_dir(self):
        """cleanupDeletesSessionFiles.no-work-dir: cleanup exits 0 when DARK_FACTORY_WORK_DIR is unset."""
        env = dict(os.environ)
        env.pop("DARK_FACTORY_WORK_DIR", None)

        result = subprocess.run(
            ["bash", CLEANUP_SCRIPT],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0
        assert "no-work-dir" in result.stderr
