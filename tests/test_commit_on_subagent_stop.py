"""
Unit tests for commit-on-subagent-stop.sh.

All tests execute the actual shell script via subprocess.run() and assert
real behavior: exit codes, commit creation, stderr output.

Flow: hook-fired
"""

import os
import subprocess
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMIT_HOOK = os.path.join(
    REPO_ROOT, "agents", "dark-factory", "scripts", "commit-on-subagent-stop.sh"
)


def init_temp_git_repo():
    """Create a temp directory with a git repo and a configured user."""
    tmp = tempfile.mkdtemp()
    subprocess.run(["git", "init", tmp], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", tmp, "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", tmp, "config", "user.name", "Test User"],
        check=True, capture_output=True,
    )
    return tmp


def stage_file(repo_dir, filename="file.txt", content="hello"):
    """Write a file to the repo and stage it."""
    path = os.path.join(repo_dir, filename)
    with open(path, "w") as f:
        f.write(content)
    subprocess.run(["git", "-C", repo_dir, "add", filename], check=True, capture_output=True)


def run_hook(agent_type, work_dir=None, env_override=None):
    """Run commit-on-subagent-stop.sh with the given agent_type on stdin."""
    env = dict(os.environ)
    if work_dir is not None:
        env["DARK_FACTORY_WORK_DIR"] = work_dir
    elif "DARK_FACTORY_WORK_DIR" in env:
        del env["DARK_FACTORY_WORK_DIR"]
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", COMMIT_HOOK],
        input=agent_type,
        capture_output=True,
        text=True,
        env=env,
    )


def get_commit_count(repo_dir):
    result = subprocess.run(
        ["git", "-C", repo_dir, "rev-list", "--count", "HEAD"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return 0
    return int(result.stdout.strip())


def get_last_commit_message(repo_dir):
    result = subprocess.run(
        ["git", "-C", repo_dir, "log", "-1", "--format=%s"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# Flow: hook-fired
# ---------------------------------------------------------------------------


class TestHookFiredSkeletonAgentStopsWithChanges:
    """Flow: hook-fired — path: hook-fired.skeleton-agent-stops-with-changes"""

    def test_hook_fired_skeleton_agent_stops_with_changes(self):
        # Plan path: hook-fired.skeleton-agent-stops-with-changes
        # Arrange: temp git repo with a staged change
        repo = init_temp_git_repo()
        stage_file(repo)

        # Act: run the hook with agent_type=skeleton-agent
        result = run_hook("skeleton-agent", work_dir=repo)

        # Assert: exits 0 and a commit was created with message "skeleton"
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        assert get_commit_count(repo) == 1, "Expected exactly one commit to be created"
        assert get_last_commit_message(repo) == "skeleton", (
            f"Expected commit message 'skeleton', got '{get_last_commit_message(repo)}'"
        )


class TestHookFiredTestingAgentStopsWithChanges:
    """Flow: hook-fired — path: hook-fired.testing-agent-stops-with-changes"""

    def test_hook_fired_testing_agent_stops_with_changes(self):
        # Plan path: hook-fired.testing-agent-stops-with-changes
        # Arrange: temp git repo with a staged change
        repo = init_temp_git_repo()
        stage_file(repo)

        # Act: run the hook with agent_type=testing-agent
        result = run_hook("testing-agent", work_dir=repo)

        # Assert: exits 0 and a commit was created with message "tests"
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        assert get_commit_count(repo) == 1, "Expected exactly one commit to be created"
        assert get_last_commit_message(repo) == "tests", (
            f"Expected commit message 'tests', got '{get_last_commit_message(repo)}'"
        )


class TestHookFiredImplementationAgentStopsWithChanges:
    """Flow: hook-fired — path: hook-fired.implementation-agent-stops-with-changes"""

    def test_hook_fired_implementation_agent_stops_with_changes(self):
        # Plan path: hook-fired.implementation-agent-stops-with-changes
        # Arrange: temp git repo with a staged change
        repo = init_temp_git_repo()
        stage_file(repo)

        # Act: run the hook with agent_type=implementation-agent
        result = run_hook("implementation-agent", work_dir=repo)

        # Assert: exits 0 and a commit was created with message "implementation"
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        assert get_commit_count(repo) == 1, "Expected exactly one commit to be created"
        assert get_last_commit_message(repo) == "implementation", (
            f"Expected commit message 'implementation', got '{get_last_commit_message(repo)}'"
        )


class TestHookFiredNoStagedChanges:
    """Flow: hook-fired — path: hook-fired.no-staged-changes"""

    def test_hook_fired_no_staged_changes(self):
        # Plan path: hook-fired.no-staged-changes
        # Arrange: temp git repo with NO staged changes
        repo = init_temp_git_repo()
        # Do NOT stage anything

        # Act: run the hook (agent_type is one of the three valid types)
        result = run_hook("skeleton-agent", work_dir=repo)

        # Assert: exits 0, NO commit was created, and stderr contains a skip log message
        # (the pseudocode says "log message to stderr" when skipping)
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        assert get_commit_count(repo) == 0, (
            "Expected no commit when there are no staged changes"
        )
        assert result.stderr.strip() != "", (
            "Expected a skip log message on stderr when no staged changes are found"
        )


class TestHookFiredUnknownAgentType:
    """Flow: hook-fired — path: hook-fired.unknown-agent-type"""

    def test_hook_fired_unknown_agent_type(self):
        # Plan path: hook-fired.unknown-agent-type
        # Arrange: temp git repo with staged changes (to confirm no commit happens despite changes)
        repo = init_temp_git_repo()
        stage_file(repo)

        # Act: run the hook with an unrecognized agent_type
        result = run_hook("unknown-agent", work_dir=repo)

        # Assert: exits 0 (non-blocking), no commit made, stderr contains recognition failure message
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
        assert get_commit_count(repo) == 0, (
            "Expected no commit for unrecognized agent_type"
        )
        assert "unknown-agent" in result.stderr, (
            "Expected agent_type name in stderr log message"
        )


class TestHookFiredWorkDirNotSet:
    """Flow: hook-fired — path: hook-fired.dark-factory-work-dir-not-set"""

    def test_hook_fired_work_dir_not_set(self):
        # Plan path: hook-fired.dark-factory-work-dir-not-set
        # Arrange: run hook without setting DARK_FACTORY_WORK_DIR and without pointer file
        # Remove the pointer file temporarily to test the true "not set" case
        pointer_file = "/tmp/dark-factory-work-dir"
        pointer_backup = None
        if os.path.exists(pointer_file):
            with open(pointer_file, "r") as f:
                pointer_backup = f.read()
            os.remove(pointer_file)

        try:
            result = run_hook("skeleton-agent", work_dir=None)

            # Assert: exits 0 (non-blocking) and logs that env var is not set
            assert result.returncode == 0, (
                f"Expected exit 0 when DARK_FACTORY_WORK_DIR not set, got {result.returncode}. stderr: {result.stderr}"
            )
            # stderr should contain a message about the env var not being set or work_dir being empty
            assert ("DARK_FACTORY_WORK_DIR" in result.stderr or "skipping commit" in result.stderr), (
                "Expected skip message in stderr when work_dir is not available"
            )
        finally:
            # Restore the pointer file
            if pointer_backup is not None:
                with open(pointer_file, "w") as f:
                    f.write(pointer_backup)


class TestHookFiredWorkDirFromPointerFile:
    """Flow: hook-fired — path: hook-fired.dark-factory-work-dir-from-pointer-file"""

    def test_hook_fired_work_dir_from_pointer_file(self):
        # Plan path: hook-fired.dark-factory-work-dir-from-pointer-file
        # Arrange: create a temp git repo and set up the pointer file, then run hook without DARK_FACTORY_WORK_DIR env var
        repo = init_temp_git_repo()
        stage_file(repo)

        pointer_file = "/tmp/dark-factory-work-dir"
        pointer_backup = None
        if os.path.exists(pointer_file):
            with open(pointer_file, "r") as f:
                pointer_backup = f.read()

        try:
            # Write the repo path to the pointer file
            with open(pointer_file, "w") as f:
                f.write(repo)

            # Act: run the hook without setting DARK_FACTORY_WORK_DIR (it should read from pointer file)
            result = run_hook("skeleton-agent", work_dir=None)

            # Assert: exits 0 and a commit was created using the pointer file path
            assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
            assert get_commit_count(repo) == 1, "Expected exactly one commit to be created from pointer file fallback"
            assert get_last_commit_message(repo) == "skeleton", (
                f"Expected commit message 'skeleton', got '{get_last_commit_message(repo)}'"
            )
        finally:
            # Restore the pointer file
            if pointer_backup is not None:
                with open(pointer_file, "w") as f:
                    f.write(pointer_backup)
            elif os.path.exists(pointer_file):
                os.remove(pointer_file)


class TestHookFiredGitCommandFailure:
    """Flow: hook-fired — path: hook-fired.git-command-failure"""

    def test_hook_fired_git_command_failure(self):
        # Plan path: hook-fired.git-command-failure
        # Arrange: provide an invalid DARK_FACTORY_WORK_DIR so git commands will fail
        result = run_hook("skeleton-agent", work_dir="/nonexistent/path/that/does/not/exist")

        # Assert: exits 0 (non-blocking even on git failure) and logs something to stderr
        assert result.returncode == 0, (
            f"Expected exit 0 even on git failure (non-blocking), got {result.returncode}. stderr: {result.stderr}"
        )
        # stderr should contain some indication of the failure
        assert result.stderr.strip() != "", (
            "Expected error message in stderr when git commands fail"
        )
