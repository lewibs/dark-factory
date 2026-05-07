"""
Test that dark-factory-agent commits metrics.csv to the feature branch.

Asserts that Step 12 in dark-factory-agent.md:
1. Writes metrics to $WORK_DIR/metrics.csv (not $projectDir/metrics.csv)
2. Stages and commits metrics.csv to the feature branch
3. Copies metrics.csv back to $projectDir/metrics.csv
"""

import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DARK_FACTORY_AGENT_PATH = os.path.join(
    REPO_ROOT, "agents", "dark-factory", "agents", "dark-factory-agent.md"
)


def _full(path):
    with open(path) as f:
        return f.read()


class TestMetricsCommittedToPR:
    """metricsCommittedToPR: metrics.csv is committed to the feature branch as part of the PR."""

    def test_metrics_written_to_work_dir(self):
        """
        metricsCommittedToPR.write-to-workdir: update-metrics.py must target $WORK_DIR/metrics.csv
        so the file ends up on the feature branch, not only in the main project directory.
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        # Must reference WORK_DIR for the csv path, not just projectDir
        assert '"$WORK_DIR/metrics.csv"' in content or "$WORK_DIR/metrics.csv" in content, (
            "dark-factory-agent Step 12 must write metrics.csv to $WORK_DIR so it lands "
            "on the feature branch. Found --csv pointing to projectDir only."
        )

    def test_metrics_csv_committed_to_branch(self):
        """
        metricsCommittedToPR.commit-to-branch: after flushing metrics, dark-factory-agent
        must stage and commit metrics.csv so it lands in the PR.
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        # Look for git add metrics.csv followed by git commit
        assert "git -C" in content and "add metrics.csv" in content, (
            "dark-factory-agent Step 12 must run 'git -C \"$WORK_DIR\" add metrics.csv' "
            "to stage the updated metrics file for the PR commit."
        )
        assert "git -C" in content and "commit" in content and "metrics.csv" in content, (
            "dark-factory-agent Step 12 must commit metrics.csv to the feature branch "
            "so it appears in the PR diff."
        )

    def test_metrics_csv_pushed_to_remote(self):
        """
        metricsCommittedToPR.push-to-remote: dark-factory-agent must push the metrics
        commit so the PR branch on the remote includes metrics.csv.
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        # Look for push in the metrics section (Step 12)
        step12_match = re.search(
            r"# Step 12.*?(?=# Step 13|## cleanup|## Rules)",
            content,
            re.DOTALL,
        )
        assert step12_match is not None, "Could not find Step 12 section in dark-factory-agent.md"
        step12 = step12_match.group(0)
        assert "push" in step12, (
            "dark-factory-agent Step 12 must push after committing metrics.csv so the "
            "remote PR branch includes the metrics update."
        )

    def test_metrics_csv_copied_back_to_project_dir(self):
        """
        metricsCommittedToPR.copy-back: dark-factory-agent must copy metrics.csv from
        $WORK_DIR back to $projectDir after committing, so the local main project dir
        stays current even before the PR is merged.
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        step12_match = re.search(
            r"# Step 12.*?(?=# Step 13|## cleanup|## Rules)",
            content,
            re.DOTALL,
        )
        assert step12_match is not None, "Could not find Step 12 section in dark-factory-agent.md"
        step12 = step12_match.group(0)
        assert "$projectDir/metrics.csv" in step12, (
            "dark-factory-agent Step 12 must copy metrics.csv back to $projectDir/metrics.csv "
            "so the local working copy stays current after cleanup."
        )

    def test_metrics_allowed_tools_include_git_ops(self):
        """
        metricsCommittedToPR.allowed-tools: dark-factory-agent frontmatter must allow
        git add, git diff, git commit, and git push so the metrics commit is not blocked.
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert frontmatter_match is not None, "Could not find YAML frontmatter"
        frontmatter = frontmatter_match.group(1)
        assert "git -C * add *" in frontmatter, (
            "allowed-tools must include 'Bash(git -C * add *)' for metrics staging"
        )
        assert "git -C * commit *" in frontmatter, (
            "allowed-tools must include 'Bash(git -C * commit *)' for metrics commit"
        )
        assert "git -C * push *" in frontmatter, (
            "allowed-tools must include 'Bash(git -C * push *)' for metrics push"
        )
