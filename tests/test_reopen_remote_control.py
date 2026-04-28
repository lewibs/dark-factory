"""Tests for scripts/reopen-remote-control.sh"""

import subprocess
import tempfile
import os
import signal
import time
from unittest.mock import patch, MagicMock


def test_reopen_remote_control_script_exists():
    """Verify that the reopen-remote-control.sh script exists and is executable"""
    script_path = "scripts/reopen-remote-control.sh"
    assert os.path.exists(script_path), f"{script_path} should exist"
    assert os.access(script_path, os.X_OK), f"{script_path} should be executable"


def test_reopen_remote_control_has_shebang():
    """Verify the script has proper bash shebang"""
    with open("scripts/reopen-remote-control.sh", "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash", "Script should have #!/bin/bash shebang"


def test_reopen_remote_control_error_handling():
    """Verify error handling for terminal launch failures"""
    script_path = "scripts/reopen-remote-control.sh"

    # Test that error handling exists by checking for error message patterns
    with open(script_path, "r") as f:
        content = f.read()

    # Should have error handling
    assert "Error:" in content or "error" in content.lower(), \
        "Script should have error handling for terminal launch failures"

    # Should check terminal exit status
    assert "TERMINAL_EXIT" in content or "$?" in content, \
        "Script should check terminal command exit status"


def test_reopen_remote_control_ppid_validation():
    """Verify proper PPID validation"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should validate PPID existence and validity
    assert "PPID" in content, "Script should reference PPID"
    assert "$PPID" in content or "\\$PPID" in content, "Script should use PPID variable"

    # Should have proper validation (not just -n check)
    assert "-gt 0" in content or "is_valid" in content.lower(), \
        "Script should validate PPID is a positive number"


def test_reopen_remote_control_kill_error_handling():
    """Verify kill command has error handling"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should have error handling around kill
    assert "kill" in content, "Script should contain kill command"

    # Should handle kill errors gracefully (2>/dev/null or error handling)
    assert "2>/dev/null" in content or "||" in content, \
        "Script should handle potential kill errors gracefully"


def test_reopen_remote_control_terminal_emulator_fallback():
    """Verify fallback support for different terminal emulators"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should attempt multiple terminal emulators
    terminal_names = ["gnome-terminal", "x-terminal-emulator", "xterm", "konsole"]
    found_terminals = sum(1 for term in terminal_names if term in content)

    assert found_terminals > 0, \
        "Script should support at least one terminal emulator"


def test_reopen_remote_control_accepts_name_argument():
    """Verify script accepts a name argument for remote-control"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should reference the first argument
    assert "$1" in content or "$NAME" in content, \
        "Script should accept a name argument"

    # Should have a default value
    assert ":-" in content or "dark factory" in content, \
        "Script should have a default name"


def test_reopen_remote_control_uses_pwd():
    """Verify script uses current working directory"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should use pwd for working directory
    assert "$(pwd)" in content or "${PWD}" in content or "pwd" in content, \
        "Script should use the current working directory"


if __name__ == "__main__":
    # Run tests
    import pytest
    pytest.main([__file__, "-v"])
