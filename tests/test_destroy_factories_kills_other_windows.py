"""
Regression test for bug: destroy-factories skips all gnome-terminal windows because
all windows share a single gnome-terminal-server daemon PID.

Root cause: find_claude_terminals() identified the calling terminal's ancestor as
gnome-terminal-server (a shared daemon). all_terminal_emulator_pids() returned the same
gnome-terminal-server PID. The exclusion check `terminal_pid == own_ancestor_pid` then
skipped ALL terminal entries, so nothing got killed.

Fix: use vte-spawn cgroup scopes (via systemctl --user list-units) to identify
individual gnome-terminal windows. Each window has a unique vte-spawn-<uuid>.scope.
The caller's own scope is read from /proc/$$/cgroup and excluded; all others with a
claude descendant are stopped.
"""

import os
import re

SCRIPT_PATH = "scripts/destroy-factories.sh"


def _read_script():
    with open(SCRIPT_PATH, "r") as f:
        return f.read()


def test_find_claude_terminals_enumerates_by_scope_not_daemon_pid():
    """
    find_claude_scope_terminals must enumerate terminal windows by their vte-spawn
    cgroup scopes via systemctl --user list-units, NOT by gnome-terminal-server daemon PID.

    The bug: all gnome-terminal windows share ONE gnome-terminal-server PID.
    find_terminal_ancestor($$) returned that shared daemon PID as the "own ancestor."
    all_terminal_emulator_pids() returned the same daemon PID.
    The exclusion check matched ALL entries → zero terminals found → nothing killed.

    The fix: enumerate all active vte-spawn-*.scope units via
    `systemctl --user list-units --type=scope 'vte-spawn-*'`, then exclude only the
    scope matching /proc/$$/cgroup. Each window is individually addressable.
    """
    content = _read_script()

    # The script must use systemctl list-units to enumerate scopes
    assert "list-units" in content, (
        "find_claude_scope_terminals must enumerate terminal windows via "
        "`systemctl --user list-units 'vte-spawn-*'`, NOT by gnome-terminal-server "
        "daemon PID. All gnome-terminal windows share a single gnome-terminal-server PID, "
        "so the own-ancestor exclusion silently skips ALL windows, causing zero kills."
    )


def test_own_window_excluded_by_scope_not_by_daemon_pid():
    """
    The script must exclude its own window by matching its OWN vte-spawn scope
    (read from /proc/$$/cgroup), not by matching the shared gnome-terminal-server PID.

    If the exclusion is PID-based (find_terminal_ancestor $$), every window gets
    excluded because they all share the same daemon PID.
    """
    content = _read_script()

    # Must read own scope from /proc/$$/cgroup (possibly with quoting like /proc/"$$"/cgroup)
    has_own_cgroup_read = (
        "/proc/$$/cgroup" in content
        or '/proc/"$$"/cgroup' in content
    )
    assert has_own_cgroup_read, (
        "Script must read /proc/$$/cgroup to identify the calling terminal's own "
        "vte-spawn scope. Excluding by gnome-terminal-server daemon PID incorrectly "
        "excludes ALL windows since they share that daemon."
    )

    # The own scope should be stored in a named variable and used in exclusion
    assert "SELF_SCOPE" in content, (
        "Script must capture its own vte-spawn scope as SELF_SCOPE from "
        "/proc/$$/cgroup and skip that scope when enumerating other terminal windows. "
        "This replaces the buggy find_terminal_ancestor approach that matches all "
        "windows to the same shared daemon PID."
    )


def test_kill_loop_uses_scope_stop():
    """
    The kill loop must stop other factory terminal scopes via
    `systemctl --user stop <scope>`. This is the correct way to close individual
    gnome-terminal windows identified by their vte-spawn scope.
    """
    content = _read_script()

    # The script must use systemctl --user stop for scopes in the kill loop
    # (beyond just the self-close step at the end)
    assert re.search(r'systemctl\s+--user\s+stop\s+"\$scope"', content) or \
           re.search(r'systemctl\s+--user\s+stop\s+\$scope', content), (
        "Script must stop other factory terminal scopes via "
        "`systemctl --user stop \"$scope\"` in the kill loop. "
        "This is the correct way to close individual gnome-terminal windows "
        "when all share a single gnome-terminal-server daemon."
    )


def test_find_claude_scope_terminals_function_exists():
    """
    The script must define a find_claude_scope_terminals function (or equivalent)
    that enumerates scopes rather than daemon PIDs.
    """
    content = _read_script()

    assert "find_claude_scope_terminals" in content, (
        "Script must define find_claude_scope_terminals() to enumerate individual "
        "terminal windows by their vte-spawn cgroup scopes. "
        "This replaces the PID-based find_claude_terminals approach that fails "
        "when all windows share a single gnome-terminal-server daemon PID."
    )


def test_scope_main_pid_function_exists():
    """
    The script must have a way to get the main PID for a scope (to check for
    claude descendants). This can be done via `systemctl --user show <scope> --property=MainPID`.
    """
    content = _read_script()

    assert "MainPID" in content or "scope_main_pid" in content, (
        "Script must retrieve the main PID for a vte-spawn scope "
        "(via `systemctl --user show <scope> --property=MainPID`) so it can "
        "check whether that window has a claude descendant before killing it."
    )


def test_script_still_has_shebang_and_name_default():
    """Sanity: script must still have shebang and default name."""
    content = _read_script()
    assert content.startswith("#!/bin/bash"), "Script must have #!/bin/bash shebang"
    assert "dark factory" in content, "Script must still default to 'dark factory'"


def test_script_still_spawns_new_terminal_after_killing():
    """After killing other factory windows, script must still spawn a new one."""
    content = _read_script()
    assert "open_terminal" in content, (
        "Script must still call open_terminal to spawn a fresh factory terminal "
        "after killing other windows."
    )


def test_script_still_self_closes():
    """After spawning the new terminal, script must still close its own window."""
    content = _read_script()
    assert "SELF_SCOPE" in content, (
        "Script must still self-close by stopping its own vte-spawn scope (SELF_SCOPE)."
    )
