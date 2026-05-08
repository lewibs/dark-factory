"""
Unit tests for scripts/update-metrics.py

Tests cover:
- New CSV created with correct headers when csv_path does not exist
- Row upsert increments runs and accumulates sums
- Averages recomputed correctly from sums
- No-metrics key in brain.json creates empty CSV (for git add to work)
- Missing usage fields in metrics data default to 0
- Script exits 0 on missing brain.json (non-fatal)
"""

import csv
import json
import os
import subprocess
import sys
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPDATE_METRICS = os.path.join(REPO_ROOT, "scripts", "update-metrics.py")
CSV_FIELDNAMES = ["agent", "skill", "avg_runtime", "avg_tokens", "runs", "sum_runtime", "sum_tokens"]


def run_script(csv_path, brain_path):
    """Run update-metrics.py as a subprocess and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, UPDATE_METRICS, "--csv", csv_path, "--brain", brain_path],
        capture_output=True,
        text=True,
    )


def write_brain(tmpdir, metrics=None):
    """Write a brain.json with optional metrics section; return the path."""
    brain = {
        "taskDescription": "test",
        "taskName": "test",
        "workDir": tmpdir,
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
    path = os.path.join(tmpdir, "brain.json")
    with open(path, "w") as f:
        json.dump(brain, f)
    return path


def read_csv_rows(csv_path):
    """Return list of row dicts from csv_path; empty list if file absent."""
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# csvInitialization tests
# ---------------------------------------------------------------------------


class TestCsvInitialization:
    """Flow: csvInitialization"""

    def test_new_file_created_with_headers(self):
        """csvInitialization.new-file: CSV is created with correct header row when absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(
                tmpdir,
                metrics={"feature-agent/planning-agent": {"elapsed_ms": 1000, "tokens": 500, "runs": 1}},
            )

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            assert os.path.exists(csv_path)

            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                assert reader.fieldnames == CSV_FIELDNAMES

    def test_existing_file_is_read_and_updated(self):
        """csvInitialization.existing-file: existing CSV rows are preserved and updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")

            # Pre-populate CSV with one row
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                writer.writeheader()
                writer.writerow({
                    "agent": "feature-agent",
                    "skill": "planning-agent",
                    "avg_runtime": "1000.0",
                    "avg_tokens": "500.0",
                    "runs": "1",
                    "sum_runtime": "1000.0",
                    "sum_tokens": "500.0",
                })

            brain_path = write_brain(
                tmpdir,
                metrics={"feature-agent/planning-agent": {"elapsed_ms": 2000, "tokens": 1000, "runs": 1}},
            )

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 1
            assert int(rows[0]["runs"]) == 2
            assert float(rows[0]["sum_runtime"]) == pytest.approx(3000.0)


# ---------------------------------------------------------------------------
# orchestratorFlushesCSV tests
# ---------------------------------------------------------------------------


class TestOrchestratorFlushesCSV:
    """Flow: orchestratorFlushesCSV"""

    def test_success_upserts_new_row(self):
        """orchestratorFlushesCSV.success: new agent/skill pair creates a CSV row with correct values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(
                tmpdir,
                metrics={
                    "feature-agent/planning-agent": {
                        "elapsed_ms": 4523.1,
                        "tokens": 12400,
                        "runs": 3,
                    }
                },
            )

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 1
            row = rows[0]
            assert row["agent"] == "feature-agent"
            assert row["skill"] == "planning-agent"
            assert int(row["runs"]) == 3
            assert float(row["sum_runtime"]) == pytest.approx(4523.1)
            assert float(row["sum_tokens"]) == pytest.approx(12400.0)
            assert float(row["avg_runtime"]) == pytest.approx(4523.1 / 3)
            assert float(row["avg_tokens"]) == pytest.approx(12400.0 / 3)

    def test_no_metrics_is_noop(self):
        """orchestratorFlushesCSV.no-metrics: brain.json with no metrics key creates empty CSV for git add."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(tmpdir)  # no metrics key

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            # CSV should be created (even with no metrics) so git add doesn't fail
            assert os.path.exists(csv_path), "CSV should be created even when there are no metrics"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 0, "CSV should have no data rows when no metrics provided"

    def test_empty_metrics_is_noop(self):
        """orchestratorFlushesCSV.empty-metrics: empty metrics dict creates empty CSV for git add."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(tmpdir, metrics={})

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            # CSV should be created (even with empty metrics) so git add doesn't fail
            assert os.path.exists(csv_path), "CSV should be created even when metrics dict is empty"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 0, "CSV should have no data rows when metrics dict is empty"

    def test_script_error_is_nonfatal(self):
        """orchestratorFlushesCSV.script-error: missing brain.json exits 0 (non-fatal)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            missing_brain = os.path.join(tmpdir, "nonexistent.json")

            result = run_script(csv_path, missing_brain)

            assert result.returncode == 0
            assert "error" in result.stderr.lower() or "cannot read" in result.stderr

    def test_missing_usage_fields_default_to_zero(self):
        """Missing elapsed_ms and tokens fields default to 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(
                tmpdir,
                metrics={
                    "some-agent": {
                        # no elapsed_ms, no tokens — only runs
                        "runs": 2,
                    }
                },
            )

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 1
            assert int(rows[0]["runs"]) == 2
            assert float(rows[0]["sum_runtime"]) == pytest.approx(0.0)
            assert float(rows[0]["sum_tokens"]) == pytest.approx(0.0)
            assert float(rows[0]["avg_runtime"]) == pytest.approx(0.0)
            assert float(rows[0]["avg_tokens"]) == pytest.approx(0.0)

    def test_upsert_increments_runs_and_accumulates(self):
        """Row upsert for the same agent/skill increments runs and accumulates sums correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")

            # First run
            brain_path = write_brain(
                tmpdir,
                metrics={"execution-agent": {"elapsed_ms": 1000, "tokens": 200, "runs": 1}},
            )
            run_script(csv_path, brain_path)

            # Second run — same key
            brain_path2 = write_brain(
                tmpdir,
                metrics={"execution-agent": {"elapsed_ms": 3000, "tokens": 400, "runs": 1}},
            )
            result = run_script(csv_path, brain_path2)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 1
            assert int(rows[0]["runs"]) == 2
            assert float(rows[0]["sum_runtime"]) == pytest.approx(4000.0)
            assert float(rows[0]["sum_tokens"]) == pytest.approx(600.0)
            assert float(rows[0]["avg_runtime"]) == pytest.approx(2000.0)
            assert float(rows[0]["avg_tokens"]) == pytest.approx(300.0)

    def test_averages_recomputed_correctly(self):
        """Averages are recomputed from accumulated sums, not raw history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(
                tmpdir,
                metrics={
                    "doc-agent": {"elapsed_ms": 6000, "tokens": 900, "runs": 3}
                },
            )

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            rows = read_csv_rows(csv_path)
            assert float(rows[0]["avg_runtime"]) == pytest.approx(2000.0)
            assert float(rows[0]["avg_tokens"]) == pytest.approx(300.0)

    def test_key_without_slash_uses_empty_skill(self):
        """Metrics key without '/' produces agent=key, skill=''."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(
                tmpdir,
                metrics={"planning-agent": {"elapsed_ms": 500, "tokens": 100, "runs": 1}},
            )

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            rows = read_csv_rows(csv_path)
            assert rows[0]["agent"] == "planning-agent"
            assert rows[0]["skill"] == ""

    def test_multiple_keys_produce_multiple_rows(self):
        """Multiple metrics keys produce one CSV row each."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "metrics.csv")
            brain_path = write_brain(
                tmpdir,
                metrics={
                    "feature-agent/planning-agent": {"elapsed_ms": 1000, "tokens": 100, "runs": 1},
                    "feature-agent/execution-agent": {"elapsed_ms": 2000, "tokens": 200, "runs": 1},
                },
            )

            result = run_script(csv_path, brain_path)

            assert result.returncode == 0, f"stderr: {result.stderr}"
            rows = read_csv_rows(csv_path)
            assert len(rows) == 2
            skills = {r["skill"] for r in rows}
            assert skills == {"planning-agent", "execution-agent"}
