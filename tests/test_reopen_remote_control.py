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


def test_reopen_remote_control_sends_sighup_to_ppid():
    """Verify the script sends SIGHUP to $PPID to close the current terminal tab"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should use kill -HUP targeting $PPID
    assert "kill -HUP" in content and "$PPID" in content, \
        "Script should send SIGHUP to $PPID to close the current terminal tab"


def test_reopen_remote_control_guards_ppid_gt_1():
    """Verify the script only sends SIGHUP when PPID > 1"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should guard against sending SIGHUP to PID 1 or below
    assert '"-gt 1"' in content or "\"$PPID\" -gt 1" in content or "$PPID\" -gt 1" in content, \
        "Script should guard against sending SIGHUP when PPID <= 1"


def test_reopen_remote_control_sighup_only_on_success():
    """Verify the script only sends SIGHUP after the new terminal opens successfully"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # TERMINAL_EXIT check must appear before the kill -HUP
    terminal_exit_idx = content.find("TERMINAL_EXIT")
    kill_hup_idx = content.find("kill -HUP")
    assert terminal_exit_idx != -1, "Script should check TERMINAL_EXIT"
    assert kill_hup_idx != -1, "Script should contain kill -HUP"
    assert terminal_exit_idx < kill_hup_idx, \
        "Script should check TERMINAL_EXIT before sending SIGHUP"


def test_reopen_remote_control_sighup_silently_fails_in_non_terminal():
    """Verify the script silently ignores errors when SIGHUP is not accepted (non-terminal context)"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # kill -HUP should have error suppression so it fails silently in non-terminal contexts
    assert "2>/dev/null" in content, \
        "Script should suppress kill errors so it fails silently in non-terminal contexts"
    assert "|| true" in content, \
        "Script should use '|| true' so a failing kill does not abort the script"


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


def test_reopen_remote_control_supported_terminal_emulators():
    """Verify the script supports multiple terminal emulators in open_terminal"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # The open_terminal function should attempt multiple terminal emulators
    required_terms = [
        "gnome-terminal",
        "xterm",
        "konsole",
        "x-terminal-emulator",
    ]
    for term in required_terms:
        assert term in content, \
            f"Script should support '{term}' as a terminal emulator in open_terminal"


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
