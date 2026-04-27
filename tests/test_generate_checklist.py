import subprocess
import json
import os
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CHECKLIST_SCRIPT = REPO_ROOT / "scripts/generate_checklist.sh"
HOOK_SCRIPT = REPO_ROOT / "agents/dark-factory/scripts/pre-tool-use-hook.sh"


def run_checklist(*args):
    return subprocess.run(
        ["bash", str(CHECKLIST_SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def run_hook(tool_input, env=None):
    env_vars = os.environ.copy()
    env_vars.pop("DARK_FACTORY_WORK_DIR", None)
    if env:
        env_vars.update(env)
    return subprocess.run(
        ["bash", str(HOOK_SCRIPT)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env_vars,
        cwd=str(REPO_ROOT),
    )


@pytest.fixture
def brain_env(tmp_path):
    brain = {"phases": {}, "metrics": {}}
    (tmp_path / "brain.json").write_text(json.dumps(brain))
    return {"DARK_FACTORY_WORK_DIR": str(tmp_path)}


# ---------------------------------------------------------------------------
# generateChecklist
# ---------------------------------------------------------------------------

def test_generate_checklist_success():
    result = run_checklist("Read plan", "Write tests", "Confirm failures")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data["todos"]) == 3
    assert data["todos"][0] == {"id": "1", "content": "Read plan", "status": "pending"}
    assert data["todos"][1] == {"id": "2", "content": "Write tests", "status": "pending"}
    assert data["todos"][2] == {"id": "3", "content": "Confirm failures", "status": "pending"}


def test_generate_checklist_empty():
    result = run_checklist()
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data == {"todos": []}


def test_generate_checklist_single():
    result = run_checklist("only item")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data["todos"]) == 1
    assert data["todos"][0] == {"id": "1", "content": "only item", "status": "pending"}


def test_generate_checklist_special_chars():
    item = 'item with "quotes" and spaces'
    result = run_checklist(item)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data["todos"]) == 1
    assert data["todos"][0]["content"] == item
    assert data["todos"][0]["status"] == "pending"
    assert data["todos"][0]["id"] == "1"


# ---------------------------------------------------------------------------
# preHookInjectsChecklist
# ---------------------------------------------------------------------------

def test_pre_hook_injects_checklist_known_agent(brain_env):
    tool_input = {
        "tool_name": "Agent",
        "tool_input": {
            "subagent_type": "testing-agent",
            "prompt": "original prompt text",
        },
    }
    result = run_hook(tool_input, env=brain_env)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    prompt = output["tool_input"]["prompt"]
    assert "TodoWrite" in prompt
    assert "original prompt text" in prompt


def test_pre_hook_injects_checklist_unknown_agent(brain_env):
    tool_input = {
        "tool_name": "Agent",
        "tool_input": {
            "subagent_type": "not-a-known-agent",
            "prompt": "original prompt",
        },
    }
    result = run_hook(tool_input, env=brain_env)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    prompt = output["tool_input"].get("prompt", "")
    assert "TodoWrite" not in prompt
    assert "original prompt" in prompt


def test_pre_hook_injects_checklist_no_brain():
    tool_input = {
        "tool_name": "Agent",
        "tool_input": {
            "subagent_type": "testing-agent",
            "prompt": "original prompt",
        },
    }
    result = run_hook(tool_input)  # no DARK_FACTORY_WORK_DIR
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output == tool_input


def test_pre_hook_non_agent_tool(brain_env):
    tool_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "echo hello",
        },
    }
    result = run_hook(tool_input, env=brain_env)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    tool_prompt = output.get("tool_input", {}).get("prompt", "")
    assert "TodoWrite" not in tool_prompt
