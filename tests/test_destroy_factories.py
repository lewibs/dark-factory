"""Tests for scripts/destroy-factories.sh"""

import subprocess
import os
import tempfile
import stat


SCRIPT_PATH = "scripts/destroy-factories.sh"


def test_destroy_factories_reads_own_cgroup_scope():
    """
    Script must delegate to close-factory.sh which reads its own vte-spawn scope from /proc/$$/cgroup
    to identify which terminal to close.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Must delegate to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"

    # Verify close-factory.sh has the implementation
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    # Must read /proc/$$/cgroup
    assert "/proc/$$/cgroup" in close_factory_content or '/proc/"$$"/cgroup' in close_factory_content, \
        "close-factory.sh should read /proc/$$/cgroup to find own vte-spawn scope"

    # Must extract scope name
    assert "vte-spawn" in close_factory_content, \
        "close-factory.sh should extract vte-spawn scope from cgroup"


def test_destroy_factories_stops_own_scope():
    """
    Script must delegate to close-factory.sh which uses systemctl --user stop to close its own vte-spawn scope.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Must delegate to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"

    # Verify close-factory.sh has the implementation
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    # Must use systemctl to stop the scope
    assert "systemctl --user stop" in close_factory_content, \
        "close-factory.sh should use systemctl --user stop to close own scope"

    # Must reference SCOPE variable
    assert "SCOPE" in close_factory_content, \
        "close-factory.sh should store scope in SCOPE variable"


def test_destroy_factories_kills_ancestor_claude():
    """
    Script must delegate to close-factory.sh which walks up the process tree and kills the ancestor claude process.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Must delegate to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"

    # Verify close-factory.sh has the implementation
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    # Must walk process tree
    assert "while" in close_factory_content or "for" in close_factory_content, \
        "close-factory.sh should walk process tree to find ancestor"

    # Must check for claude process
    assert "claude" in close_factory_content, \
        "close-factory.sh should check for 'claude' process name"

    # Must use kill
    assert "kill " in close_factory_content or "kill\t" in close_factory_content, \
        "close-factory.sh should use kill to terminate ancestor"


def test_destroy_factories_exits_cleanly():
    """
    Script must delegate to close-factory.sh which exits cleanly.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # destroy-factories.sh just delegates
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"

    # Verify the script is simple - it should have the bash call to delegate
    # (the shebang has "bash" too, but we're checking for the delegation pattern)
    assert 'bash "$(dirname "$0")/close-factory.sh"' in content, \
        "Script should call close-factory.sh using bash"


def test_destroy_factories_no_open_terminal():
    """
    Script must not spawn or open any new terminal.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    assert "open_terminal" not in content, \
        "Script should not call open_terminal function"

    assert "gnome-terminal" not in content, \
        "Script should not spawn gnome-terminal"

    assert "x-terminal-emulator" not in content, \
        "Script should not spawn x-terminal-emulator"


def test_destroy_factories_removes_helper_functions():
    """
    Script must not contain the old helper functions that tried to kill other terminals.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Old functions that should be removed
    assert "find_claude_scope_terminals" not in content, \
        "Script should not define find_claude_scope_terminals"

    assert "find_claude_terminals" not in content, \
        "Script should not define find_claude_terminals"

    assert "has_claude_descendant" not in content, \
        "Script should not define has_claude_descendant"

    assert "open_terminal" not in content, \
        "Script should not define open_terminal"

    assert "all_vte_scopes" not in content, \
        "Script should not define all_vte_scopes"

    assert "scope_main_pid" not in content, \
        "Script should not define scope_main_pid"


def test_destroy_factories_no_name_parameter():
    """
    Script should not have a NAME parameter or accept arguments.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    assert "NAME=" not in content, \
        "Script should not have NAME parameter"

    assert "$1" not in content, \
        "Script should not reference command-line arguments"


def test_destroy_factories_script_exists_and_executable():
    """Verify the script exists and is executable"""
    assert os.path.exists(SCRIPT_PATH), f"{SCRIPT_PATH} should exist"
    assert os.access(SCRIPT_PATH, os.X_OK), f"{SCRIPT_PATH} should be executable"


def test_destroy_factories_has_shebang():
    """Verify the script has a bash shebang"""
    with open(SCRIPT_PATH, "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash", "Script should have #!/bin/bash shebang"


def test_destroy_factories_self_close_only():
    """
    Script must only close itself, not kill other terminals.
    The presence of loop functions like find_claude_scope_terminals or
    all_vte_scopes that enumerate ALL terminals should be gone.
    destroy-factories.sh delegates to close-factory.sh which implements self-close-only.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Should NOT have kill loops that iterate over multiple scopes
    assert "for scope in $(all_vte_scopes)" not in content, \
        "Script should not iterate over all vte scopes"

    assert "for scope in $(find_claude_scope_terminals)" not in content, \
        "Script should not iterate over multiple claude terminals"

    # Should delegate to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"

    # Verify close-factory.sh has only one self-close logic
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    scope_stops = close_factory_content.count("systemctl --user stop")
    assert scope_stops == 1, \
        f"close-factory.sh should have exactly one systemctl --user stop call (found {scope_stops})"
