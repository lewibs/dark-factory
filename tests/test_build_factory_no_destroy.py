"""
Regression test: build-factory must NOT close/destroy the calling terminal session.

The build-factory command should open a new gnome-terminal window running
claude /remote-control and leave the calling session entirely untouched.
"""

import os


COMMANDS_DIR = "commands"
SCRIPTS_DIR = "scripts"
BUILD_FACTORY_CMD = os.path.join(COMMANDS_DIR, "build-factory.md")
BUILD_FACTORY_SCRIPT = os.path.join(SCRIPTS_DIR, "build-factory.sh")
OPEN_FACTORY_SCRIPT = os.path.join(SCRIPTS_DIR, "open-factory.sh")
REOPEN_SCRIPT = os.path.join(SCRIPTS_DIR, "reopen-remote-control.sh")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Tests: command wiring
# ---------------------------------------------------------------------------

def test_build_factory_command_exists():
    """commands/build-factory.md must exist."""
    assert os.path.exists(BUILD_FACTORY_CMD), f"{BUILD_FACTORY_CMD} should exist"


def test_build_factory_command_does_not_call_reopen_script():
    """build-factory.md must NOT delegate to reopen-remote-control.sh.

    reopen-remote-control.sh unconditionally kills the calling terminal after
    opening the new one.  build-factory must use a separate open-only script.
    """
    content = _read(BUILD_FACTORY_CMD)
    assert "reopen-remote-control.sh" not in content, (
        "build-factory.md must not call reopen-remote-control.sh — "
        "that script destroys the calling terminal session"
    )


def test_build_factory_command_calls_build_factory_script():
    """build-factory.md must call scripts/build-factory.sh (open-only)."""
    content = _read(BUILD_FACTORY_CMD)
    assert "build-factory.sh" in content, (
        "build-factory.md must delegate to scripts/build-factory.sh"
    )


# ---------------------------------------------------------------------------
# Tests: open-only script exists and has no self-close logic
# ---------------------------------------------------------------------------

def test_build_factory_script_exists():
    """scripts/build-factory.sh must exist."""
    assert os.path.exists(BUILD_FACTORY_SCRIPT), (
        f"{BUILD_FACTORY_SCRIPT} should exist"
    )


def test_build_factory_script_is_executable():
    """scripts/build-factory.sh must be executable."""
    assert os.access(BUILD_FACTORY_SCRIPT, os.X_OK), (
        f"{BUILD_FACTORY_SCRIPT} should be executable"
    )


def test_build_factory_script_has_shebang():
    """scripts/build-factory.sh must have a bash shebang."""
    content = _read(BUILD_FACTORY_SCRIPT)
    first_line = content.splitlines()[0].strip()
    assert first_line == "#!/bin/bash", (
        "scripts/build-factory.sh should start with #!/bin/bash"
    )


def test_build_factory_script_has_no_scope_stop():
    """scripts/build-factory.sh must NOT contain systemctl scope stop logic.

    Stopping the vte-spawn cgroup scope closes the calling terminal tab.
    """
    content = _read(BUILD_FACTORY_SCRIPT)
    assert "systemctl --user stop" not in content, (
        "scripts/build-factory.sh must not stop any systemctl scope — "
        "doing so would close the calling terminal"
    )
    assert "vte-spawn" not in content, (
        "scripts/build-factory.sh must not reference vte-spawn scopes"
    )


def test_build_factory_script_has_no_claude_ancestor_kill():
    """scripts/build-factory.sh must NOT walk the process tree to kill claude.

    Killing the ancestor claude process destroys the calling factory session.
    """
    content = _read(BUILD_FACTORY_SCRIPT)
    # The self-close pattern: walk up from $$ looking for 'claude' and kill it
    assert 'pid=$$' not in content, (
        "scripts/build-factory.sh must not walk the process tree from $$ "
        "to find and kill an ancestor claude process"
    )
    # Allow kill only if it is not the claude-ancestor-kill pattern.
    # Specifically, the dangerous pattern is kill "$pid" inside a while loop
    # that started from $$ checking for the name 'claude'.
    # We already guard via pid=$$ check above, but double-check for
    # the name-comparison guard too.
    if '"claude"' in content:
        # If 'claude' appears in the script it should only be in the terminal
        # launch command, not in a kill path.
        assert 'kill "$pid"' not in content, (
            "scripts/build-factory.sh must not kill a process found by "
            "walking the ancestor tree for 'claude'"
        )


def test_build_factory_script_opens_terminal():
    """scripts/build-factory.sh must delegate to open-factory.sh for terminal opening."""
    content = _read(BUILD_FACTORY_SCRIPT)
    assert "open-factory.sh" in content, (
        "scripts/build-factory.sh should delegate to open-factory.sh"
    )
    # Verify open-factory.sh has the terminal emulator logic
    open_factory_content = _read(OPEN_FACTORY_SCRIPT)
    terminal_emulators = ["gnome-terminal", "x-terminal-emulator", "xterm", "konsole"]
    found = [t for t in terminal_emulators if t in open_factory_content]
    assert len(found) > 0, (
        "scripts/open-factory.sh should reference at least one terminal emulator"
    )


def test_build_factory_script_launches_remote_control():
    """scripts/build-factory.sh must launch claude in remote-control mode."""
    content = _read(BUILD_FACTORY_SCRIPT)
    assert "remote-control" in content, (
        "scripts/build-factory.sh must launch claude with /remote-control"
    )


def test_build_factory_script_uses_working_directory():
    """scripts/open-factory.sh must respect the current working directory."""
    # Since build-factory.sh delegates to open-factory.sh, verify open-factory.sh
    # handles the working directory
    open_factory_content = _read(OPEN_FACTORY_SCRIPT)
    assert "$(pwd)" in open_factory_content or "${PWD}" in open_factory_content or "pwd" in open_factory_content, (
        "scripts/open-factory.sh should use the current working directory"
    )


# ---------------------------------------------------------------------------
# Tests: open-factory.sh exists and has the terminal opening logic
# ---------------------------------------------------------------------------

def test_open_factory_script_exists():
    """scripts/open-factory.sh must exist."""
    assert os.path.exists(OPEN_FACTORY_SCRIPT), (
        f"{OPEN_FACTORY_SCRIPT} should exist"
    )


def test_open_factory_script_is_executable():
    """scripts/open-factory.sh must be executable."""
    assert os.access(OPEN_FACTORY_SCRIPT, os.X_OK), (
        f"{OPEN_FACTORY_SCRIPT} should be executable"
    )


def test_open_factory_script_has_shebang():
    """scripts/open-factory.sh must have a bash shebang."""
    content = _read(OPEN_FACTORY_SCRIPT)
    first_line = content.splitlines()[0].strip()
    assert first_line == "#!/bin/bash", (
        "scripts/open-factory.sh should start with #!/bin/bash"
    )


def test_build_factory_delegates_to_open_factory():
    """scripts/build-factory.sh must delegate to open-factory.sh."""
    content = _read(BUILD_FACTORY_SCRIPT)
    assert "open-factory.sh" in content, (
        "scripts/build-factory.sh should call open-factory.sh"
    )
    # Verify it passes the NAME parameter
    assert "$NAME" in content, (
        "scripts/build-factory.sh should pass the NAME parameter to open-factory.sh"
    )


# ---------------------------------------------------------------------------
# Ensure reopen-remote-control.sh retains its self-close logic (unchanged)
# ---------------------------------------------------------------------------

def test_reopen_remote_control_still_has_self_close_logic():
    """reopen-remote-control.sh must still delegate to close-factory.sh for self-close."""
    content = _read(REOPEN_SCRIPT)
    assert "close-factory.sh" in content, (
        "reopen-remote-control.sh should delegate self-close to close-factory.sh"
    )
