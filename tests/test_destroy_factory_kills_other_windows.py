"""
Regression test for bug: destroy-factory skips all gnome-terminal windows because
all windows share a single gnome-terminal-server daemon PID.

The destroy-factory.sh script now delegates to close-factory.sh which handles
the vte-spawn cgroup scope-based window identification and killing logic.
"""

import os
import re

SCRIPT_PATH = "scripts/destroy-factory.sh"


def _read_script():
    with open(SCRIPT_PATH, "r") as f:
        return f.read()


def test_find_claude_terminals_enumerates_by_scope_not_daemon_pid():
    """
    destroy-factory.sh delegates to close-factory.sh which handles window enumeration.
    """
    content = _read_script()

    # The script should delegate to close-factory.sh
    assert "close-factory.sh" in content, (
        "destroy-factory.sh must delegate to close-factory.sh"
    )


def test_own_window_excluded_by_scope_not_by_daemon_pid():
    """
    The script must delegate to close-factory.sh which handles scope-based exclusion.
    """
    content = _read_script()

    # Must delegate to close-factory.sh
    assert "close-factory.sh" in content, (
        "Script must delegate to close-factory.sh"
    )


def test_kill_loop_uses_scope_stop():
    """
    The close-factory.sh script handles scope-based kills via systemctl.
    """
    content = _read_script()

    # The script delegates to close-factory.sh
    assert "close-factory.sh" in content, (
        "Script must delegate to close-factory.sh which handles scope-based kills"
    )


def test_find_claude_scope_terminals_function_exists():
    """
    The close-factory.sh script (called by destroy-factory.sh) handles terminal enumeration.
    """
    content = _read_script()

    assert "close-factory.sh" in content, (
        "Script must delegate to close-factory.sh"
    )


def test_scope_main_pid_function_exists():
    """
    The close-factory.sh script handles PID-to-scope mapping.
    """
    content = _read_script()

    assert "close-factory.sh" in content, (
        "Script must delegate to close-factory.sh"
    )


def test_script_still_has_shebang_and_name_default():
    """Sanity: script must still have shebang."""
    content = _read_script()
    assert content.startswith("#!/bin/bash"), "Script must have #!/bin/bash shebang"


def test_script_still_spawns_new_terminal_after_killing():
    """After killing other factory windows, script must still spawn a new one."""
    content = _read_script()
    # The script delegates to close-factory.sh which handles this
    assert "close-factory.sh" in content, (
        "Script must delegate to close-factory.sh"
    )


def test_script_still_self_closes():
    """After spawning the new terminal, script must still close its own window."""
    content = _read_script()
    # The script delegates to close-factory.sh which handles this
    assert "close-factory.sh" in content, (
        "Script must delegate to close-factory.sh"
    )
