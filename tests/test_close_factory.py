"""Tests for scripts/close-factory.sh"""

import os


def test_close_factory_script_exists():
    """Verify that the close-factory.sh script exists and is executable"""
    script_path = "scripts/close-factory.sh"
    assert os.path.exists(script_path), f"{script_path} should exist"
    assert os.access(script_path, os.X_OK), f"{script_path} should be executable"


def test_close_factory_has_shebang():
    """Verify the script has proper bash shebang"""
    with open("scripts/close-factory.sh", "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash", "Script should have #!/bin/bash shebang"


def test_close_factory_reads_cgroup_scope():
    """Verify the script reads its own vte-spawn scope from /proc/$$/cgroup"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should read /proc/$$/cgroup
    assert "/proc/$$/cgroup" in content, \
        "Script should read /proc/$$/cgroup to find the current tab's scope"

    # Should look for vte-spawn pattern
    assert "vte-spawn-" in content, \
        "Script should look for a vte-spawn-*.scope cgroup entry"

    # Should extract to SCOPE variable
    assert "SCOPE" in content, \
        "Script should extract scope into SCOPE variable"


def test_close_factory_stops_scope():
    """Verify the script stops the cgroup scope using systemctl"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should use systemctl --user stop
    assert "systemctl --user stop" in content, \
        "Script should stop the scope with systemctl --user stop"

    # Should reference the SCOPE variable
    assert 'systemctl --user stop "$SCOPE"' in content or \
           "systemctl --user stop $SCOPE" in content, \
        "Script should stop the SCOPE variable"


def test_close_factory_guards_against_empty_scope():
    """Verify the script only stops scope if it exists"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should check if SCOPE is non-empty before stopping
    assert '[ -n "$SCOPE" ]' in content, \
        "Script should guard with [ -n \"$SCOPE\" ] before stopping"


def test_close_factory_errors_suppress_silently():
    """Verify systemctl stop errors are suppressed"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should suppress systemctl errors
    assert "2>/dev/null" in content, \
        "Script should suppress systemctl errors with 2>/dev/null"

    # Should use || true to continue on error
    assert "|| true" in content, \
        "Script should use || true so errors don't abort"


def test_close_factory_uses_head_1():
    """Verify the script uses head -1 to limit scope extraction"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should limit to one scope with head -1
    assert "head -1" in content, \
        "Script should use head -1 to extract only one scope"


def test_close_factory_walks_process_tree():
    """Verify the script walks up the process tree"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should start from current PID
    assert 'pid=$$' in content, \
        "Script should start the process-tree walk from $$"

    # Should loop through parents
    assert "while" in content and '[ "$pid" -gt 1 ]' in content, \
        "Script should use while loop to walk process tree"


def test_close_factory_gets_parent_pid():
    """Verify the script retrieves parent PID"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should use ps to get parent PID
    assert 'ppid=$(ps -o ppid=' in content, \
        "Script should use ps -o ppid= to get parent PID"


def test_close_factory_gets_process_name():
    """Verify the script retrieves process name"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should use ps to get process name
    assert 'name=$(ps -o comm=' in content, \
        "Script should use ps -o comm= to get process name"


def test_close_factory_checks_for_claude():
    """Verify the script checks for 'claude' process"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should check if process name is claude
    assert '"claude"' in content, \
        "Script should check whether the process name equals 'claude'"


def test_close_factory_kills_claude():
    """Verify the script kills the ancestor claude process"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should use kill command
    assert 'kill "$pid"' in content, \
        "Script should kill the process when its name matches 'claude'"

    # Should suppress errors on kill
    assert 'kill "$pid" 2>/dev/null || true' in content, \
        "Script should suppress errors when killing claude"


def test_close_factory_breaks_after_kill():
    """Verify the script breaks after killing claude"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should have a break statement after kill
    assert "break" in content, \
        "Script should break after killing ancestor claude"


def test_close_factory_guards_against_low_pids():
    """Verify the script never walks below PID 1"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Loop condition must guard against PID <= 1
    assert '[ "$pid" -gt 1 ]' in content, \
        "Script should guard the loop with [ \"$pid\" -gt 1 ] to never kill PID 1 or below"

    # Inner guard against low ppid
    assert '"$ppid" -le 1' in content, \
        "Script should break when ppid drops to 1 or below"


def test_close_factory_no_terminal_logic():
    """Verify script does not contain terminal opening logic"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should not have terminal opening logic
    assert "open_terminal" not in content, \
        "Script should not contain open_terminal function or calls"

    assert "gnome-terminal" not in content, \
        "Script should not spawn gnome-terminal"

    assert "x-terminal-emulator" not in content, \
        "Script should not spawn x-terminal-emulator"

    assert "xterm" not in content, \
        "Script should not spawn xterm"

    assert "konsole" not in content, \
        "Script should not spawn konsole"


def test_close_factory_no_claude_slash_remote_control():
    """Verify script does not contain claude /remote-control logic"""
    with open("scripts/close-factory.sh", "r") as f:
        content = f.read()

    # Should not have remote-control logic
    assert "/remote-control" not in content, \
        "Script should not contain /remote-control command"

    # Should not have NAME variable for remote-control
    assert "NAME=" not in content, \
        "Script should not have NAME variable for remote-control"

    # Should not call open_terminal or similar
    assert "open_terminal" not in content, \
        "Script should not call open_terminal"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
