---
name: test-bash-script-content-assertions
description: "How to test bash scripts that have untestable side effects (GUI spawning, terminal opening, process killing) by asserting structure and key patterns in the script's source text rather than executing it."
user-invocable: false
---
## When to use

When writing pytest tests for a bash script that:
- Spawns a GUI window or terminal emulator (cannot be run headlessly in CI)
- Kills external processes (dangerous to run against real processes in tests)
- Requires hardware/display infrastructure that is not available in test environments

In these cases, subprocess execution is impractical or unsafe. Instead, assert that the script's source text contains the structural patterns required to implement the correct behavior.

## Steps

### 1. Open the script as text, not as an executable

```python
SCRIPT_PATH = "scripts/my-script.sh"

def test_my_script_has_correct_structure():
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()
    # assertions follow
```

Use a relative path from the repo root. Tests should be run from the repo root (the same location as `pytest.ini` or `pyproject.toml`).

### 2. Assert for functional behavior, not line-by-line text

Each test should map to one observable behavior path from the plan. Assertions should check for:

- **Function existence**: `assert "my_function_name" in content`
- **Safety guards**: `assert "$$" in content` (script uses its own PID for self-exclusion)
- **Error handling**: `assert "exit 1" in content or "exit $" in content`
- **Fallback chains**: `assert "||" in content` (script uses `||` for graceful degradation)
- **Known string literals**: `assert "dark factory" in content` (default argument value)

```python
def test_script_excludes_own_ancestor():
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()
    assert "$$" in content, "Script should use $$ to identify its own PID"
    assert "own_ancestor" in content or "continue" in content, \
        "Script should skip its own ancestor terminal"
```

### 3. Add a sanity-check test for file existence and executability

Always include a basic test confirming the file exists and is executable:

```python
import os, stat

def test_script_exists_and_is_executable():
    assert os.path.exists(SCRIPT_PATH), f"{SCRIPT_PATH} should exist"
    assert os.access(SCRIPT_PATH, os.X_OK), f"{SCRIPT_PATH} should be executable"

def test_script_has_shebang():
    with open(SCRIPT_PATH, "r") as f:
        first_line = f.readline().strip()
    assert first_line == "#!/bin/bash", "Script should have #!/bin/bash shebang"
```

### 4. Map each plan path to one test function

Name each test `test_<script>_<path-name>` and include the plan path in the docstring:

```python
def test_destroy_factory_kill_failed():
    """
    # Plan path: destroy-factory.kill-failed
    One or more terminals could not be killed; warns to stderr, continues to spawn.
    """
    with open(SCRIPT_PATH, "r") as f:
        content = f.read()
    assert "||" in content, "Script should use || to handle kill failure gracefully"
    assert ">&2" in content or "2>/dev/null" in content, \
        "Script should warn on kill failure (write to stderr)"
```

### 5. Combine content assertions with case-insensitive checks for prose messages

For error/warning messages that may vary in capitalization:

```python
assert "error" in content.lower() or "Error" in content, \
    "Script should print an error message when spawn fails"
```

## Notes

- Content assertions do not prove the script runs correctly — they prove it has the structural elements required to implement the described behavior. This is the appropriate trade-off for scripts with untestable side effects.
- Do not over-specify: check for the presence of key identifiers (`kill`, `open_terminal`, `$$`) rather than exact syntax, since bash allows multiple valid formulations.
- Always include `f"stderr: ..."` in assert failure messages when running subprocess-based tests, but for content tests, describe what is missing: `"Script should call open_terminal to spawn a fresh factory terminal"`.
- See also: `test-bash-hook-scripts-with-pytest` for scripts that CAN be executed via subprocess (hook scripts with stdin/stdout contracts).
- This pattern appeared in `tests/test_destroy_factory.py` for testing `scripts/destroy-factory.sh`, which spawns terminal emulators and kills other processes.
