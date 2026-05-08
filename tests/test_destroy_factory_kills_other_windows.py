"""
Regression test: ensure destroy-factory no longer attempts to kill other terminals.

The old implementation tried to enumerate all vte-spawn scopes and kill those with
claude descendants (except its own). This was removed in favor of a self-close-only approach.

This test file verifies that the old code patterns are completely removed.
"""

import os
import re

SCRIPT_PATH = "scripts/destroy-factory.sh"


def _read_script():
    with open(SCRIPT_PATH, "r") as f:
        return f.read()


def test_script_does_not_enumerate_all_terminals():
    """
    Script must not enumerate all vte-spawn scopes via systemctl list-units.
    The old code called all_vte_scopes() to get every terminal window.
    New self-close-only code does not do this.
    """
    content = _read_script()

    assert "list-units" not in content, (
        "Script should not use systemctl list-units to enumerate terminal windows. "
        "Self-close-only approach should not enumerate other terminals."
    )

    assert "all_vte_scopes" not in content, (
        "Script should not define or call all_vte_scopes(). "
        "This function enumerated all terminal scopes — removed in self-close-only design."
    )


def test_script_does_not_loop_over_scopes():
    """
    Script must not have a loop that iterates over multiple terminal scopes.
    The old code had: for scope in $(find_claude_scope_terminals); do stop $scope; done
    The new code directly closes its own scope without looping.
    """
    content = _read_script()

    # Should not have loop over found scopes
    assert "for scope in" not in content, (
        "Script should not loop over multiple scopes. "
        "Self-close-only approach targets only the current terminal."
    )

    assert "find_claude_scope_terminals" not in content, (
        "Script should not define or call find_claude_scope_terminals(). "
        "This function enumerated all terminal windows with claude descendants — "
        "removed in self-close-only design."
    )


def test_script_does_not_check_for_claude_descendants():
    """
    The old code checked whether each terminal had a claude descendant process.
    New self-close-only code does not do this — it just closes itself.
    """
    content = _read_script()

    assert "has_claude_descendant" not in content, (
        "Script should not define or call has_claude_descendant(). "
        "Self-close-only approach does not need to check other terminals for descendants."
    )

    assert "scope_main_pid" not in content, (
        "Script should not define or call scope_main_pid(). "
        "This function retrieved main PIDs to check for claude descendants in other terminals."
    )


def test_script_does_not_spawn_new_terminal():
    """
    Script must not open/spawn any new terminal.
    The old code had open_terminal() which launched a new terminal before closing itself.
    New code simply closes without spawning anything.
    """
    content = _read_script()

    assert "open_terminal" not in content, (
        "Script should not define or call open_terminal(). "
        "Self-close-only approach does not spawn anything."
    )

    assert "gnome-terminal" not in content, (
        "Script should not invoke gnome-terminal to spawn a new window."
    )

    assert "x-terminal-emulator" not in content, (
        "Script should not invoke x-terminal-emulator to spawn a new window."
    )

    assert "xterm" not in content, (
        "Script should not invoke xterm to spawn a new window."
    )

    assert "konsole" not in content, (
        "Script should not invoke konsole to spawn a new window."
    )


def test_script_does_not_have_fallback_terminal_logic():
    """
    The old code had find_claude_terminals() as a fallback for non-GNOME systems.
    New code does not need this fallback since it only self-closes.
    """
    content = _read_script()

    assert "find_claude_terminals" not in content, (
        "Script should not define or call find_claude_terminals(). "
        "This fallback enumerated terminals by process name — no longer needed for self-close."
    )

    assert r"xterm\|konsole" not in content, (
        "Script should not reference fallback terminal names like xterm or konsole."
    )


def test_script_reads_own_scope_only():
    """
    Script must delegate to close-factory.sh which reads its own vte-spawn scope from /proc/$$/cgroup.
    It should NOT enumerate other scopes.
    """
    content = _read_script()

    # Must delegate to close-factory.sh
    assert "close-factory.sh" in content, (
        "destroy-factory.sh must delegate to close-factory.sh which handles scopes."
    )

    # Verify close-factory.sh has the actual implementation
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    # Must read /proc/$$/cgroup
    has_own_cgroup_read = (
        "/proc/$$/cgroup" in close_factory_content
        or '/proc/"$$"/cgroup' in close_factory_content
    )
    assert has_own_cgroup_read, (
        "close-factory.sh must read /proc/$$/cgroup to identify its own vte-spawn scope."
    )

    # Must store in SCOPE (or similar) variable for the single self-close operation
    assert "SCOPE" in close_factory_content, (
        "close-factory.sh must extract its own scope into a SCOPE variable."
    )


def test_script_stops_only_own_scope():
    """
    Script must delegate to close-factory.sh which calls systemctl --user stop exactly once on its own scope.
    No loops, no enumeration of other scopes.
    """
    content = _read_script()

    # Must delegate to close-factory.sh
    assert "close-factory.sh" in content, (
        "destroy-factory.sh must delegate to close-factory.sh."
    )

    # Verify close-factory.sh has the actual implementation
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    # Count systemctl stop calls in close-factory.sh
    stop_calls = close_factory_content.count("systemctl --user stop")
    assert stop_calls == 1, (
        f"close-factory.sh should have exactly one 'systemctl --user stop' call (found {stop_calls}). "
        "Self-close-only approach targets only the current terminal."
    )

    # Should reference SCOPE variable, not loop over scopes
    assert "systemctl --user stop \"$SCOPE\"" in close_factory_content or \
           "systemctl --user stop $SCOPE" in close_factory_content, (
        "close-factory.sh must stop $SCOPE (its own scope), not enumerate and kill others."
    )


def test_script_still_has_shebang():
    """Sanity: script must still have shebang."""
    content = _read_script()
    assert content.startswith("#!/bin/bash"), "Script must have #!/bin/bash shebang"


def test_script_exits_cleanly():
    """
    destroy-factory.sh must delegate to close-factory.sh which exits cleanly.
    No spawn logic, no complex error handling.
    """
    content = _read_script()

    # destroy-factory.sh just delegates
    assert "close-factory.sh" in content, (
        "destroy-factory.sh must delegate to close-factory.sh."
    )

    # Verify close-factory.sh exists and has proper structure
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    assert close_factory_content.startswith("#!/bin/bash"), (
        "close-factory.sh must have #!/bin/bash shebang."
    )


def test_script_kills_ancestor_claude():
    """
    close-factory.sh must walk up the process tree and kill the ancestor claude process.
    This is the second part of self-close: after stopping the scope,
    also kill the claude parent process. destroy-factory.sh delegates this.
    """
    content = _read_script()

    # Must delegate to close-factory.sh
    assert "close-factory.sh" in content, (
        "destroy-factory.sh must delegate to close-factory.sh."
    )

    # Verify close-factory.sh has the actual implementation
    with open("scripts/close-factory.sh", "r") as f:
        close_factory_content = f.read()

    # Must walk process tree (not enumerate all terminals)
    assert "while" in close_factory_content or "for pid in" not in close_factory_content, (
        "close-factory.sh should use while loop to walk process tree, not for loop over terminals."
    )

    # Must check for claude process name
    assert '"claude"' in close_factory_content or "'claude'" in close_factory_content or '= "claude"' in close_factory_content, (
        "close-factory.sh must check for 'claude' process name when walking up process tree."
    )

    # Must kill the ancestor
    assert "kill " in close_factory_content or "kill\t" in close_factory_content, (
        "close-factory.sh must use kill to terminate ancestor claude process."
    )

    # Must break after finding and killing claude (not continue loop)
    assert "break" in close_factory_content, (
        "close-factory.sh should break after killing ancestor claude."
    )


def test_no_logging_or_complex_flow():
    """
    Script should be minimal: no logging, no multiple code paths, no complex branching.
    Just read scope, stop it, kill ancestor, exit.
    """
    content = _read_script()

    # Should not have logging functions
    assert "_log" not in content, (
        "Script should not have logging functions (_log)."
    )

    # Should not have flow path indicators in comments (success/none-found/kill-failed)
    # These indicate complex multi-path logic
    assert "# Plan path:" not in content, (
        "Script should not have plan path flow documentation. "
        "Self-close is straightforward with no branching logic."
    )
