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

    def test_reset_command_has_flow_messages(self):
        """Test that the reset command defines expected flow outputs."""
        command_path = os.path.join(
            os.path.dirname(__file__),
            "../commands/reset.md"
        )
        with open(command_path, "r") as f:
            content = f.read()
            # Should have error flows
            assert "reset.not-git-repo" in content
            assert "reset.no-main-worktree" in content
            assert "reset.checkout-failed" in content
            assert "reset.pull-failed" in content
            # Should have success flow
            assert "reset.success" in content

    def test_reset_command_has_bash_implementation(self):
        """Test that the reset command contains direct Bash implementation."""
        command_path = os.path.join(
            os.path.dirname(__file__),
            "../commands/reset.md"
        )
        with open(command_path, "r") as f:
            content = f.read()
            assert "git rev-parse --show-toplevel" in content, \
                "Command should check git root"
            assert "worktree list" in content, \
                "Command should list worktrees"

    def test_reset_command_checks_git_root(self):
        """Test that the reset command checks for git root."""
        command_path = os.path.join(
            os.path.dirname(__file__),
            "../commands/reset.md"
        )
        with open(command_path, "r") as f:
            content = f.read()
            assert "git rev-parse --show-toplevel" in content, \
                "Command should check git root"

    def test_reset_command_finds_main_worktree(self):
        """Test that the reset command attempts to find main worktree."""
        command_path = os.path.join(
            os.path.dirname(__file__),
            "../commands/reset.md"
        )
        with open(command_path, "r") as f:
            content = f.read()
            assert "worktree list" in content, \
                "Command should list git worktrees"
            assert "main" in content or "master" in content, \
                "Command should check for main or master branch"

    def test_reset_command_uses_git_commands(self):
        """Test that the reset command uses standard git commands."""
        command_path = os.path.join(
            os.path.dirname(__file__),
            "../commands/reset.md"
        )
        with open(command_path, "r") as f:
            content = f.read()
            assert "git checkout main" in content, \
                "Command should check out main"
            assert "git pull" in content, \
                "Command should pull latest code"

    def test_reset_script_does_not_exist(self):
        """Test that the external reset.sh script no longer exists."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "../agents/dark-factory/scripts/reset.sh"
        )
        assert not os.path.exists(script_path), \
            "reset.sh script should not exist (logic moved to command)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
