"""Tests for scripts/open-factory.sh"""

import os


def test_open_factory_script_exists():
    """Verify that the open-factory.sh script exists and is executable"""
    script_path = "scripts/open-factory.sh"
    assert os.path.exists(script_path), f"{script_path} should exist"
    assert os.access(script_path, os.X_OK), f"{script_path} should be executable"


def test_open_factory_has_shebang():
    """Verify the script has proper bash shebang"""
    with open("scripts/open-factory.sh", "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash", "Script should have #!/bin/bash shebang"


def test_open_factory_has_open_terminal_function():
    """Verify the script has the open_terminal function"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    assert "open_terminal()" in content, \
        "Script should define open_terminal() function"


def test_open_factory_supported_terminal_emulators():
    """Verify the script supports multiple terminal emulators"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    required_terms = [
        "gnome-terminal",
        "xterm",
        "konsole",
        "x-terminal-emulator",
    ]
    for term in required_terms:
        assert term in content, \
            f"Script should support '{term}' as a terminal emulator"


def test_open_factory_accepts_name_parameter():
    """Verify script accepts a NAME parameter"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should reference the first argument
    assert "$1" in content or "$NAME" in content, \
        "Script should accept a name argument"

    # Should have a default value
    assert ":-" in content or "dark factory" in content, \
        "Script should have a default name"


def test_open_factory_uses_current_working_directory():
    """Verify script uses current working directory for terminal"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should use pwd for working directory
    assert "$(pwd)" in content or "${PWD}" in content or "pwd" in content, \
        "Script should use the current working directory"


def test_open_factory_checks_terminal_exit_status():
    """Verify script checks terminal spawn exit status"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should store and check the exit status
    assert "TERMINAL_EXIT" in content, \
        "Script should check TERMINAL_EXIT status"

    assert "$TERMINAL_EXIT" in content, \
        "Script should reference the TERMINAL_EXIT variable"

    assert "if [ $TERMINAL_EXIT -ne 0 ]" in content, \
        "Script should check if TERMINAL_EXIT is non-zero"


def test_open_factory_exits_non_zero_on_spawn_failure():
    """Verify script exits non-zero if terminal spawn fails"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should exit with error code on failure
    assert "exit $TERMINAL_EXIT" in content, \
        "Script should exit with TERMINAL_EXIT error code on spawn failure"


def test_open_factory_exits_zero_on_success():
    """Verify script exits 0 on successful terminal spawn"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should have exit 0 on success
    assert "exit 0" in content, \
        "Script should exit with code 0 on success"


def test_open_factory_terminal_emulator_fallback_order():
    """Verify terminal emulators are checked in the right order"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Verify gnome-terminal is checked first
    gnome_idx = content.find("gnome-terminal")
    xterm_emulator_idx = content.find("x-terminal-emulator")
    xterm_idx = content.find("xterm")
    konsole_idx = content.find("konsole")

    assert gnome_idx != -1, "Script should support gnome-terminal"
    assert xterm_emulator_idx != -1, "Script should support x-terminal-emulator"
    assert xterm_idx != -1, "Script should support xterm"
    assert konsole_idx != -1, "Script should support konsole"

    # gnome-terminal should be checked before others
    assert gnome_idx < xterm_emulator_idx, \
        "gnome-terminal should be tried before x-terminal-emulator"


def test_open_factory_has_error_message_for_no_terminal():
    """Verify script has error message when no terminal emulator is found"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should have error message
    assert "Error: No terminal emulator found" in content, \
        "Script should have error message when no terminal emulator is found"

    # Should output to stderr
    assert ">&2" in content, \
        "Error message should be written to stderr"


def test_open_factory_no_close_logic():
    """Verify script does not contain close/scope/cgroup logic"""
    with open("scripts/open-factory.sh", "r") as f:
        content = f.read()

    # Should not have close-factory-like logic
    assert "/proc/$$/cgroup" not in content, \
        "Script should not read cgroup (that's close-factory.sh's job)"

    assert "systemctl --user stop" not in content, \
        "Script should not stop scopes (that's close-factory.sh's job)"

    assert "kill " not in content and "kill\t" not in content, \
        "Script should not kill processes (that's close-factory.sh's job)"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
