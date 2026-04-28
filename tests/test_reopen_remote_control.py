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


def test_reopen_remote_control_uses_cgroup_scope_to_close_tab():
    """Verify the script reads the vte-spawn scope from /proc/$$/cgroup to close the current tab"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should read cgroup to find the vte-spawn scope
    assert "/proc/$$/cgroup" in content, \
        "Script should read /proc/$$/cgroup to find the current tab's scope"
    assert "vte-spawn-" in content, \
        "Script should look for a vte-spawn-*.scope cgroup entry"
    assert "systemctl --user stop" in content, \
        "Script should stop the scope with systemctl --user stop"


def test_reopen_remote_control_skips_silently_without_scope():
    """Verify the script skips closing the tab silently when no vte-spawn scope is found"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should guard against empty SCOPE before stopping
    assert '[ -n "$SCOPE" ]' in content, \
        "Script should only stop the scope when SCOPE is non-empty (i.e. running in gnome-terminal)"


def test_reopen_remote_control_scope_stop_only_on_success():
    """Verify the script only stops the scope after the new terminal opens successfully"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # TERMINAL_EXIT check must appear before the systemctl stop
    terminal_exit_idx = content.find("TERMINAL_EXIT")
    scope_stop_idx = content.find("systemctl --user stop")
    assert terminal_exit_idx != -1, "Script should check TERMINAL_EXIT"
    assert scope_stop_idx != -1, "Script should contain systemctl --user stop"
    assert terminal_exit_idx < scope_stop_idx, \
        "Script should check TERMINAL_EXIT before stopping the scope"


def test_reopen_remote_control_scope_stop_silently_fails_in_non_terminal():
    """Verify the script silently ignores errors when not running in a gnome-terminal"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # systemctl stop should have error suppression so it fails silently in non-gnome-terminal contexts
    assert "2>/dev/null" in content, \
        "Script should suppress systemctl errors so it fails silently when not in gnome-terminal"
    assert "|| true" in content, \
        "Script should use '|| true' so a failing systemctl stop does not abort the script"


def test_reopen_remote_control_scope_stop_error_handling():
    """Verify the scope stop command has error handling"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should stop at most one scope (head -1 limits output to one line)
    assert "head -1" in content, \
        "Script should use head -1 to ensure only one scope is stopped"

    # Should handle stop errors gracefully
    assert "2>/dev/null" in content or "||" in content, \
        "Script should handle potential systemctl stop errors gracefully"


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
