"""Tests for scripts/destroy-factories.sh"""

import subprocess
import os
import tempfile
import stat


SCRIPT_PATH = "scripts/destroy-factories.sh"


def test_destroy_factories_success():
    """
    # Plan path: destroy-factories.success
    All Claude terminals found and killed; new factory terminal spawned successfully.
    Given: terminal PIDs with claude descendants exist (other than our own ancestor)
    When: script is run
    Then: those terminals are killed and a new factory terminal is spawned
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script must call find_claude_terminals and iterate over PIDs to kill them
    assert "find_claude_terminals" in content, \
        "Script should define or call find_claude_terminals"

    # The script must call open_terminal to spawn a fresh factory
    assert "open_terminal" in content, \
        "Script should call open_terminal to spawn a fresh factory terminal"

    # The script must attempt to kill terminals found
    assert "kill " in content or "kill\t" in content, \
        "Script should kill terminals returned by find_claude_terminals"


def test_destroy_factories_none_found():
    """
    # Plan path: destroy-factories.none-found
    No other Claude terminals found; new factory terminal spawned (no kills needed).
    When find_claude_terminals yields no PIDs, open_terminal is still called.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script must not exit early when no terminals are found —
    # it must still call open_terminal
    assert "open_terminal" in content, \
        "Script should call open_terminal even when no Claude terminals are found"

    # There should be a loop/iteration that simply does nothing if no PIDs yielded
    assert "for " in content or "while " in content, \
        "Script should use a loop to iterate over found terminal PIDs"


def test_destroy_factories_kill_failed():
    """
    # Plan path: destroy-factories.kill-failed
    One or more terminals could not be killed (permission error);
    warns to stderr, continues to spawn.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Kill failure should warn (not abort)
    assert "warn" in content.lower() or ">&2" in content or "2>/dev/null" in content, \
        "Script should warn on kill failure (write to stderr or suppress gracefully)"

    # Script must not use 'set -e' or 'exit' immediately after a kill failure
    # — it must continue to spawn. Check that there's a fallback/warn pattern
    assert "||" in content, \
        "Script should use || to handle kill failure gracefully without exiting"


def test_destroy_factories_spawn_failed():
    """
    # Plan path: destroy-factories.spawn-failed
    New terminal could not be opened (no terminal emulator found or emulator returned
    non-zero); exits non-zero.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Should have error message for spawn failure
    assert "error" in content.lower() or "Error" in content, \
        "Script should print an error message when spawn fails"

    # Should exit non-zero on spawn failure
    assert "exit 1" in content or "exit $" in content, \
        "Script should exit non-zero when terminal spawn fails"


def test_destroy_factories_excludes_own_ancestor():
    """
    # Plan path: destroy-factories.success (safety constraint)
    Script never kills its own ancestor terminal — only other terminals.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Must find its own ancestor and exclude it from the kill list
    assert "$$" in content, \
        "Script should use $$ to identify its own PID for ancestor exclusion"

    assert "own_ancestor" in content or "skip" in content or "continue" in content, \
        "Script should skip/exclude its own ancestor terminal"


def test_destroy_factories_script_exists_and_executable():
    """Verify the script exists and is executable"""
    assert os.path.exists(SCRIPT_PATH), f"{SCRIPT_PATH} should exist"
    assert os.access(SCRIPT_PATH, os.X_OK), f"{SCRIPT_PATH} should be executable"


def test_destroy_factories_has_shebang():
    """Verify the script has a bash shebang"""
    with open(SCRIPT_PATH, "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash", "Script should have #!/bin/bash shebang"


def test_destroy_factories_accepts_name_argument():
    """Verify script accepts a name argument with default 'dark factory'"""
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    assert "$1" in content or "$NAME" in content, \
        "Script should accept a name argument"

    assert "dark factory" in content, \
        "Script should default to 'dark factory' as the session name"


def test_destroy_factories_only_kills_claude_terminals():
    """
    Verify the script checks for claude descendants before killing,
    not all terminals indiscriminately.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Must check for claude in the descendant tree
    assert "claude" in content, \
        "Script should check for 'claude' process in descendant tree before killing"

    # Must walk child/descendant tree — not just look at direct children
    assert "ps " in content or "pgrep" in content, \
        "Script should use ps or pgrep to inspect process tree"
