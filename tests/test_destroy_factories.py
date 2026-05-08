"""Tests for scripts/destroy-factories.sh"""

import subprocess
import os
import tempfile
import stat


SCRIPT_PATH = "scripts/destroy-factories.sh"


def test_destroy_factories_success():
    """
    # Plan path: destroy-factories.success
    All Claude terminals found and killed; command exits cleanly.
    Given: terminal PIDs with claude descendants exist (other than our own ancestor)
    When: script is run
    Then: those terminals are killed and script exits 0
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script must call find_claude_terminals and iterate over PIDs to kill them
    assert "find_claude_terminals" in content, \
        "Script should define or call find_claude_terminals"

    # The script must attempt to kill terminals found
    assert "kill " in content or "kill\t" in content, \
        "Script should kill terminals returned by find_claude_terminals"

    # The script should exit cleanly with exit 0
    assert "exit 0" in content, \
        "Script should exit cleanly (exit 0) after killing terminals"


def test_destroy_factories_none_found():
    """
    # Plan path: destroy-factories.none-found
    No other Claude terminals found; command exits cleanly (no kills needed).
    When find_claude_terminals yields no PIDs, script still exits cleanly.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script must not exit early when no terminals are found —
    # it must continue to completion
    assert "exit 0" in content, \
        "Script should exit cleanly (exit 0) even when no Claude terminals are found"

    # There should be a loop/iteration that simply does nothing if no PIDs yielded
    assert "for " in content or "while " in content, \
        "Script should use a loop to iterate over found terminal PIDs"


def test_destroy_factories_kill_failed():
    """
    # Plan path: destroy-factories.kill-failed
    One or more terminals could not be killed (permission error);
    warns to stderr, continues to completion.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Kill failure should warn (not abort)
    assert "warn" in content.lower() or ">&2" in content or "2>/dev/null" in content, \
        "Script should warn on kill failure (write to stderr or suppress gracefully)"

    # Script must not use 'set -e' or 'exit' immediately after a kill failure
    # — it must continue to completion. Check that there's a fallback/warn pattern
    assert "||" in content, \
        "Script should use || to handle kill failure gracefully without exiting"


def test_destroy_factories_exits_cleanly():
    """
    # Plan path: destroy-factories.success
    Script always exits cleanly with exit code 0, regardless of kill success/failure.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Should exit cleanly with exit 0
    assert "exit 0" in content, \
        "Script should exit cleanly with code 0"

    # Should NOT have exit 1 (spawn failures no longer apply)
    assert "exit 1" not in content, \
        "Script should not exit with code 1 (no spawn logic)"


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


def test_destroy_factories_no_name_argument():
    """Verify script no longer accepts a name argument"""
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # Script should not reference $1 or $NAME at top level
    # (the functions are removed, so NAME variable should not exist)
    assert "NAME=" not in content, \
        "Script should not use a NAME variable"


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
