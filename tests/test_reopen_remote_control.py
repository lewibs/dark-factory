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


def test_reopen_remote_control_walks_process_tree():
    """Verify the script walks the process tree to find the terminal emulator ancestor"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should use ps to query parent PIDs
    assert "ps -o ppid=" in content, \
        "Script should use 'ps -o ppid=' to walk the process tree"

    # Should use ps to get process name
    assert "ps -o comm=" in content, \
        "Script should use 'ps -o comm=' to get the ancestor process name"

    # Should start the walk from $$ (current script PID)
    assert "$$" in content, \
        "Script should start the process tree walk from $$ (current script PID)"


def test_reopen_remote_control_kills_only_first_terminal_ancestor():
    """Verify the script stops after killing the first terminal emulator found"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should have a return/break immediately after killing, so it never continues
    # walking after the first match.  The function must contain a kill followed
    # by a return inside the match block.
    assert "kill_terminal_ancestor" in content, \
        "Script should define a kill_terminal_ancestor function"

    # After the kill there should be a 'return' to stop walking
    kill_idx = content.find('kill "$ppid"')
    assert kill_idx != -1, "Script should kill the ancestor by PID variable"
    after_kill = content[kill_idx:]
    assert "return" in after_kill, \
        "Script should return immediately after killing the first terminal ancestor"


def test_reopen_remote_control_never_kills_pid_1_or_below():
    """Verify the script never kills PID 1 or any PID <= 1"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # Should have a guard that stops the walk at PID 1 or below
    assert "-le 1" in content or "<= 1" in content, \
        "Script should guard against killing PID 1 or below"


def test_reopen_remote_control_skips_silently_when_no_terminal_found():
    """Verify the script skips silently when no terminal emulator is in the process tree"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # The function should simply return (or fall off the end) without printing
    # an error when no terminal emulator ancestor is found.  There should NOT
    # be an unconditional error message inside kill_terminal_ancestor after the
    # loop ends.
    func_start = content.find("kill_terminal_ancestor()")
    assert func_start != -1, "Script should define kill_terminal_ancestor function"

    # Find the closing brace of the function body
    func_body_start = content.find("{", func_start)
    # Count braces to find the matching closing brace
    depth = 0
    func_body_end = func_body_start
    for i, ch in enumerate(content[func_body_start:], start=func_body_start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                func_body_end = i
                break

    func_body = content[func_body_start:func_body_end + 1]
    # The comment about skipping silently should be present
    assert "silently" in func_body or "skip" in func_body.lower(), \
        "Script should document that it skips silently when no terminal emulator is found"


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


def test_reopen_remote_control_known_terminals_in_ancestor_check():
    """Verify all known terminal emulators are checked during the ancestor walk"""
    script_path = "scripts/reopen-remote-control.sh"

    with open(script_path, "r") as f:
        content = f.read()

    # All terminals listed in the task description must appear in the known-terms list
    required_terms = [
        "gnome-terminal",
        "gnome-terminal-server",
        "xterm",
        "konsole",
        "x-terminal-emulator",
    ]
    for term in required_terms:
        assert term in content, \
            f"Script should check for '{term}' as a known terminal emulator ancestor"


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
