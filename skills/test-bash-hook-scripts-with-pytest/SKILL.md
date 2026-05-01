---
name: test-bash-hook-scripts-with-pytest
description: "How to write pytest unit tests for PreToolUse/PostToolUse bash hook scripts by executing them via subprocess and asserting stdout JSON, file state, exit codes, and stderr."
user-invocable: false
---
## When to use

When adding or modifying pytest tests for any bash hook script under
`agents/dark-factory/scripts/` (e.g., `pre-tool-use-hook.sh`,
`post-tool-use-hook.sh`). Use this whenever a new hook script is introduced
and needs behavioral coverage.

## Steps

### 1. Derive absolute script paths from `__file__`

Never hardcode absolute paths. Derive REPO_ROOT at module load time so tests
work from any working directory:

```python
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_HOOK = os.path.join(REPO_ROOT, "agents", "dark-factory", "scripts", "pre-tool-use-hook.sh")
POST_HOOK = os.path.join(REPO_ROOT, "agents", "dark-factory", "scripts", "post-tool-use-hook.sh")
```

### 2. Build a reusable `run_hook` helper

```python
import json, subprocess

def run_hook(hook_path, stdin_payload, env_override=None):
    env = dict(os.environ)   # copy the full inherited env
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", hook_path],
        input=json.dumps(stdin_payload),
        capture_output=True,
        text=True,
        env=env,
    )
```

Key points:
- Always start from `dict(os.environ)` so the subprocess inherits PATH and
  other system vars required by `jq`, `bash`, etc.
- `env_override` is a dict of additions/overrides (e.g., `{"DARK_FACTORY_WORK_DIR": tmpdir}`).
- `text=True` makes `result.stdout` and `result.stderr` strings, not bytes.

### 3. Write brain.json to a temp directory

Use `tempfile.TemporaryDirectory()` as a context manager so cleanup is
automatic. Construct the brain dict with a `make_brain()` factory that fills
all required fields and accepts a `phases` override:

```python
import tempfile

ALL_PHASES_FALSE = {
    "prep-running": False, "prep-complete": False,
    "worker-running": False, "worker-complete": False,
    "review-running": False, "review-complete": False,
    "docs-running": False, "docs-complete": False,
    "skills-running": False, "skills-complete": False,
    "pr-running": False, "pr-complete": False,
    "cleanup-running": False, "cleanup-complete": False,
}

def make_brain(phases=None):
    base_phases = dict(ALL_PHASES_FALSE)
    if phases:
        base_phases.update(phases)
    return {
        "taskDescription": "test task",
        "taskName": "test",
        "workDir": "/tmp/test",
        "classification": "feature",
        "planFilePath": None,
        "bugFiles": None,
        "prUrl": None,
        "docsWritten": None,
        "skillsWritten": None,
        "phases": base_phases,
    }

with tempfile.TemporaryDirectory() as tmpdir:
    brain_path = os.path.join(tmpdir, "brain.json")
    with open(brain_path, "w") as f:
        json.dump(make_brain(), f)
    result = run_hook(PRE_HOOK, {"prompt": "hello"}, {"DARK_FACTORY_WORK_DIR": tmpdir})
```

### 4. Assert stdout is valid JSON (pre-hook only)

The pre-hook must emit the (possibly modified) tool input JSON on stdout.
Always parse it and assert the structure:

```python
out = json.loads(result.stdout)
assert "BRAIN STATE" in out["prompt"]
```

### 5. Read back the mutated file, not the original dict

The pre-hook mutates `brain.json` on disk (sets `*-running=true`) before
injecting its content into the prompt. Therefore, when asserting that the
injected prompt matches the brain JSON, re-read the file after the hook runs
rather than serializing the original dict:

```python
with open(brain_path) as bf:
    updated_brain = json.load(bf)
updated_brain_str = json.dumps(updated_brain, separators=(",", ":"))
assert updated_brain_str in out["prompt"]
```

### 6. Simulate absent brain (no-brain path)

To test the no-brain early-exit path, remove `DARK_FACTORY_WORK_DIR` from the
inherited env explicitly. Do not rely on it being absent — it may be set in
the developer's shell:

```python
env = dict(os.environ)
env.pop("DARK_FACTORY_WORK_DIR", None)
result = subprocess.run(["bash", PRE_HOOK], input=json.dumps(payload),
                        capture_output=True, text=True, env=env)
assert result.returncode == 0
# pre-hook: stdout must be the unchanged stdin passthrough
assert json.loads(result.stdout) == payload
# post-hook: stdout must be empty (no passthrough)
assert result.stdout == ""
```

### 7. Assert file state changes for post-hook

After running the post-hook, re-read brain.json and assert field values
and absence of the patch file:

```python
with open(brain_path) as f:
    updated = json.load(f)
assert updated["planFilePath"] == "/some/plan.md"
assert not os.path.exists(patch_path)
assert updated["phases"]["worker-running"] is False
assert updated["phases"]["worker-complete"] is True
```

### 8. Assert stderr keywords for edge-case paths

Hook scripts emit diagnostic markers to stderr. Use these to confirm edge
branches were taken:

```python
assert "phase=none" in result.stderr      # pre-hook: all phases complete
assert "no-patch" in result.stderr        # post-hook: no brain-patch.json present
assert "no running phase found" in result.stderr  # post-hook: no phase is running
```

### 9. Testing hook scripts that run git commands (e.g. SubagentStop hooks)

When the hook script itself calls `git` (e.g., `git -C "$work_dir" commit`), tests must
set up a real git repo with a committed-friendly config, because `git commit` fails without
`user.email` and `user.name`:

```python
import tempfile, subprocess, os

def init_temp_git_repo():
    """Create a temp directory with a real git repo and a configured user."""
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
    """Write a file and stage it so there are changes to commit."""
    path = os.path.join(repo_dir, filename)
    with open(path, "w") as f:
        f.write(content)
    subprocess.run(["git", "-C", repo_dir, "add", filename], check=True, capture_output=True)
```

To verify whether a commit was created and what message it has:

```python
def get_commit_count(repo_dir):
    result = subprocess.run(
        ["git", "-C", repo_dir, "rev-list", "--count", "HEAD"],
        capture_output=True, text=True,
    )
    return 0 if result.returncode != 0 else int(result.stdout.strip())

def get_last_commit_message(repo_dir):
    result = subprocess.run(
        ["git", "-C", repo_dir, "log", "-1", "--format=%s"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()
```

For `SubagentStop` hooks, pass the agent name as a plain string (not JSON) to `input=`:

```python
result = subprocess.run(
    ["bash", HOOK_SCRIPT],
    input="skeleton-agent",   # plain text, not JSON
    capture_output=True,
    text=True,
    env={**os.environ, "DARK_FACTORY_WORK_DIR": repo_dir},
)
```

## Notes

- The `bash` binary must be on PATH for `subprocess.run(["bash", hook_path])` to work. This is always true on Linux/macOS CI.
- Hook scripts must have execute permission (`chmod +x`) OR be invoked via `bash <script>` (the subprocess call above uses the latter, so chmod is not strictly required for tests).
- The pre-hook stdout is the tool-input override channel; the post-hook stdout is unused. Tests must reflect this asymmetry: assert `result.stdout == ""` for the post-hook no-brain case.
- Always include `f"stderr: {result.stderr}"` in assert messages so failures show the hook's log output.
- Phase names and their ordering in `ALL_PHASES_FALSE` must match the order declared in the actual hook scripts. If a new phase is added to the hooks, update this constant.
- `git commit` fails silently (or with error) when `user.email` and `user.name` are not configured. Always configure them in `init_temp_git_repo()` — do not assume they are inherited from the host git config, because CI environments often have no global git identity.
- `git rev-list --count HEAD` returns a non-zero exit code on a repo with zero commits (no HEAD yet). Always guard against this by checking `result.returncode != 0` and returning 0.
- See also: `claude-code-hook-stdout-reserved` skill for why stdout discipline matters in PreToolUse hooks.
- See also: `subagent-stop-hook-stdin-format` skill for the plain-text stdin format used by SubagentStop hooks.
