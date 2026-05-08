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
    """Verify error handling for terminal launch failures via open-factory.sh delegation"""
    script_path = "scripts/reopen-remote-control.sh"

    # Test that error handling exists by checking for delegation to open-factory
    with open(script_path, "r") as f:
        content = f.read()

    # Should call open-factory.sh and check its exit status
    assert "open-factory.sh" in content, \
        "Script should delegate to open-factory.sh"

    # Should check the exit status of open-factory.sh
    assert "OPEN_EXIT" in content or "$?" in content, \
        "Script should check exit status of open-factory.sh call"


def test_reopen_remote_control_uses_cgroup_scope_to_close_tab():
    """Verify the script delegates to close-factory.sh which closes the current tab"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should delegate to close-factory.sh which handles the scope closing
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh to close the current tab"

    # Verify close-factory.sh has the actual implementation
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    assert "/proc/$$/cgroup" in close_factory_content, \
        "close-factory.sh should read /proc/$$/cgroup to find the current tab's scope"
    assert "vte-spawn-" in close_factory_content, \
        "close-factory.sh should look for a vte-spawn-*.scope cgroup entry"
    assert "systemctl --user stop" in close_factory_content, \
        "close-factory.sh should stop the scope with systemctl --user stop"


def test_reopen_remote_control_skips_silently_without_scope():
    """Verify close-factory.sh skips closing the tab silently when no vte-spawn scope is found"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should guard against empty SCOPE before stopping
    assert '[ -n "$SCOPE" ]' in content, \
        "close-factory.sh should only stop the scope when SCOPE is non-empty (i.e. running in gnome-terminal)"


def test_reopen_remote_control_scope_stop_only_on_success():
    """Verify reopen-remote-control only stops the scope after the new terminal opens successfully"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # OPEN_EXIT check must appear before the close-factory call
    open_exit_idx = content.find("OPEN_EXIT")
    close_factory_idx = content.find("close-factory.sh")
    assert open_exit_idx != -1, "Script should check OPEN_EXIT"
    assert close_factory_idx != -1, "Script should delegate to close-factory.sh"
    assert open_exit_idx < close_factory_idx, \
        "Script should check OPEN_EXIT before calling close-factory.sh"


def test_reopen_remote_control_scope_stop_silently_fails_in_non_terminal():
    """Verify close-factory.sh silently ignores errors when not running in a gnome-terminal"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # systemctl stop should have error suppression so it fails silently in non-gnome-terminal contexts
    assert "2>/dev/null" in content, \
        "close-factory.sh should suppress systemctl errors so it fails silently when not in gnome-terminal"
    assert "|| true" in content, \
        "close-factory.sh should use '|| true' so a failing systemctl stop does not abort the script"


def test_reopen_remote_control_scope_stop_error_handling():
    """Verify close-factory.sh scope stop command has error handling"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should stop at most one scope (head -1 limits output to one line)
    assert "head -1" in content, \
        "close-factory.sh should use head -1 to ensure only one scope is stopped"

    # Should handle stop errors gracefully
    assert "2>/dev/null" in content or "||" in content, \
        "close-factory.sh should handle potential systemctl stop errors gracefully"


def test_reopen_remote_control_terminal_emulator_fallback():
    """Verify open-factory.sh has fallback support for different terminal emulators"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should attempt multiple terminal emulators
    terminal_names = ["gnome-terminal", "x-terminal-emulator", "xterm", "konsole"]
    found_terminals = sum(1 for term in terminal_names if term in content)

    assert found_terminals > 0, \
        "open-factory.sh should support at least one terminal emulator"


def test_reopen_remote_control_supported_terminal_emulators():
    """Verify open-factory.sh supports multiple terminal emulators"""
    with open("scripts/open-factory.sh", "r") as f:
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
            f"open-factory.sh should support '{term}' as a terminal emulator"


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
    """Verify open-factory.sh uses current working directory"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should use pwd for working directory
    assert "$(pwd)" in content or "${PWD}" in content or "pwd" in content, \
        "open-factory.sh should use the current working directory"


def test_reopen_remote_control_kills_claude_process_after_scope_stop():
    """Verify close-factory.sh walks the process tree and kills the first ancestor named 'claude'"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should walk up the process tree from $$
    assert 'pid=$$' in content, \
        "close-factory.sh should start the process-tree walk from $$"

    # Should use ps to get parent PID and process name
    assert 'ppid=$(ps -o ppid=' in content, \
        "close-factory.sh should retrieve the parent PID with ps -o ppid="
    assert 'name=$(ps -o comm=' in content, \
        "close-factory.sh should retrieve the process name with ps -o comm="

    # Should compare against the literal name 'claude'
    assert '"claude"' in content, \
        "close-factory.sh should check whether the process name equals 'claude'"

    # Should kill the found process with silent failure
    assert 'kill "$pid"' in content, \
        "close-factory.sh should kill the process when its name matches 'claude'"


def test_reopen_remote_control_kills_claude_only_after_scope_stop():
    """Verify close-factory.sh's claude-kill logic comes after the systemctl scope stop"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    scope_stop_idx = content.find("systemctl --user stop")
    kill_claude_idx = content.find('kill "$pid"')

    assert scope_stop_idx != -1, "close-factory.sh should contain systemctl --user stop"
    assert kill_claude_idx != -1, "close-factory.sh should contain the claude kill logic"
    assert scope_stop_idx < kill_claude_idx, \
        "Claude kill logic must appear after the systemctl scope stop in close-factory.sh"


def test_reopen_remote_control_never_kills_pid_1_or_below():
    """Verify close-factory.sh's loop guard prevents killing PID 1 or below"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # The while condition must guard against PID <= 1
    assert '[ "$pid" -gt 1 ]' in content, \
        "close-factory.sh should guard the loop with [ \"$pid\" -gt 1 ] to never kill PID 1 or below"

    # The inner break should also guard against ppid <= 1
    assert '"$ppid" -le 1' in content, \
        "close-factory.sh should break when ppid drops to 1 or below"


def test_reopen_remote_control_claude_kill_silent_failure():
    """Verify close-factory.sh's kill command uses silent failure so the script never aborts"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # kill line must have both 2>/dev/null and || true
    assert 'kill "$pid" 2>/dev/null || true' in content, \
        "close-factory.sh's kill command must suppress errors with 2>/dev/null and use || true for silent failure"


if __name__ == "__main__":
    # Run tests
    import pytest
    pytest.main([__file__, "-v"])
