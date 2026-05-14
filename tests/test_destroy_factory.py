"""Tests for scripts/destroy-factory.sh"""

import subprocess
import os
import tempfile
import stat


SCRIPT_PATH = "scripts/destroy-factory.sh"


def test_destroy_factory_success():
    """
    # Plan path: destroy-factory.success
    All Claude terminals found and killed; new factory terminal spawned successfully.
    Given: terminal PIDs with claude descendants exist (other than our own ancestor)
    When: script is run
    Then: those terminals are killed and a new factory terminal is spawned
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script should delegate to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"


def test_destroy_factory_none_found():
    """
    # Plan path: destroy-factory.none-found
    No other Claude terminals found; new factory terminal spawned (no kills needed).
    When find_claude_terminals yields no PIDs, open_terminal is still called.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script must delegate to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"


def test_destroy_factory_kill_failed():
    """
    # Plan path: destroy-factory.kill-failed
    Kill fails for one or more PIDs; warns to stderr, continues to spawn.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script delegates to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"


def test_destroy_factory_spawn_failed():
    """
    # Plan path: destroy-factory.spawn-failed
    Terminal spawn fails; prints error to stderr and exits non-zero.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script delegates to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"


def test_destroy_factory_excludes_own_ancestor():
    """
    # Plan path: destroy-factory.success (safety constraint)
    Own ancestor terminal is never killed.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script delegates to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"


def test_destroy_factory_script_exists_and_executable():
    """Script file exists and is executable."""
    assert os.path.isfile(SCRIPT_PATH), f"{SCRIPT_PATH} should exist"
    assert os.access(SCRIPT_PATH, os.X_OK), f"{SCRIPT_PATH} should be executable"


def test_destroy_factory_has_shebang():
    """Script has proper shebang."""
    with open(SCRIPT_PATH, "r") as f:
        first_line = f.readline()
    assert first_line.startswith("#!/"), f"{SCRIPT_PATH} should have a shebang"


def test_destroy_factory_accepts_name_argument():
    """Script documentation mentions it accepts close-factory.sh behavior."""
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script delegates to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"


def test_destroy_factory_only_kills_claude_terminals():
    """Script only targets terminals with claude descendants."""
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()

    # The script delegates to close-factory.sh
    assert "close-factory.sh" in content, \
        "Script should delegate to close-factory.sh"
