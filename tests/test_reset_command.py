"""
Unit tests for the reset command.
"""

import subprocess
import os
import tempfile
import shutil
import pytest


class TestResetCommand:
    """Tests for the reset command functionality."""

    def test_reset_script_exists(self):
        """Test that the reset script exists and is executable."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "../agents/dark-factory/scripts/reset.sh"
        )
        assert os.path.exists(script_path), "reset.sh script should exist"
        assert os.access(script_path, os.X_OK), "reset.sh should be executable"

    def test_reset_command_file_exists(self):
        """Test that the reset command Markdown file exists."""
        command_path = os.path.join(
            os.path.dirname(__file__),
            "../commands/reset.md"
        )
        assert os.path.exists(command_path), "reset.md command file should exist"

    def test_reset_command_has_description(self):
        """Test that the reset command file contains required documentation."""
        command_path = os.path.join(
            os.path.dirname(__file__),
            "../commands/reset.md"
        )
        with open(command_path, "r") as f:
            content = f.read()
            assert "description:" in content, "Command should have YAML description"
            assert "/reset" in content, "Command should document /reset usage"
            assert "main branch" in content, "Command should mention main branch"

    def test_reset_script_has_flow_messages(self):
        """Test that the reset script defines expected flow outputs."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "../agents/dark-factory/scripts/reset.sh"
        )
        with open(script_path, "r") as f:
            content = f.read()
            # Should have error flows
            assert "reset.not-git-repo" in content
            assert "reset.no-main-worktree" in content
            assert "reset.checkout-failed" in content
            assert "reset.pull-failed" in content
            # Should have success flow
            assert "reset.success" in content

    def test_reset_script_uses_proper_error_handling(self):
        """Test that the reset script uses set -euo pipefail."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "../agents/dark-factory/scripts/reset.sh"
        )
        with open(script_path, "r") as f:
            content = f.read()
            assert "set -euo pipefail" in content, \
                "Script should use proper bash error handling"

    def test_reset_script_checks_git_root(self):
        """Test that the reset script checks for git root."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "../agents/dark-factory/scripts/reset.sh"
        )
        with open(script_path, "r") as f:
            content = f.read()
            assert "git rev-parse --show-toplevel" in content, \
                "Script should check git root"

    def test_reset_script_finds_main_worktree(self):
        """Test that the reset script attempts to find main worktree."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "../agents/dark-factory/scripts/reset.sh"
        )
        with open(script_path, "r") as f:
            content = f.read()
            assert "worktree list" in content, \
                "Script should list git worktrees"
            assert "main" in content or "master" in content, \
                "Script should check for main or master branch"

    def test_reset_script_uses_git_commands(self):
        """Test that the reset script uses standard git commands."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "../agents/dark-factory/scripts/reset.sh"
        )
        with open(script_path, "r") as f:
            content = f.read()
            assert "git checkout main" in content, \
                "Script should check out main"
            assert "git pull" in content, \
                "Script should pull latest code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
