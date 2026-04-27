"""
Tests for scripts/generate_checklist.sh and pre-tool-use-hook.sh checklist injection.
Flows: generateChecklist, preHookInjectsChecklist
"""
import json
import os
import subprocess
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "generate_checklist.sh")
PRE_HOOK = os.path.join(REPO_ROOT, "agents", "dark-factory", "scripts", "pre-tool-use-hook.sh")


def run_script(*args):
    """Run generate_checklist.sh with given args and return CompletedProcess."""
    return subprocess.run(
        ["bash", SCRIPT] + list(args),
        capture_output=True,
        text=True,
    )


def run_hook(stdin_payload, env_override=None):
    env = dict(os.environ)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", PRE_HOOK],
        input=json.dumps(stdin_payload),
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# generateChecklist tests
# ---------------------------------------------------------------------------


class TestGenerateChecklistSuccess:
    """Flow: generateChecklist — happy path with multiple items."""

    def test_generateChecklist_success(self):
        """Plan path: generateChecklist.success"""
        # Arrange: two items
        result = run_script("Plan feature", "Get plan approval", "Execute plan")
        assert result.returncode == 0, f"stderr: {result.stderr}"
        out = json.loads(result.stdout)
        # Should produce 3-item TodoWriteBody
        assert "todos" in out
        todos = out["todos"]
        assert len(todos) == 3
        assert todos[0] == {"id": "1", "content": "Plan feature", "status": "pending"}
        assert todos[1] == {"id": "2", "content": "Get plan approval", "status": "pending"}
        assert todos[2] == {"id": "3", "content": "Execute plan", "status": "pending"}


class TestGenerateChecklistEmpty:
    """Flow: generateChecklist — edge case: no args."""

    def test_generateChecklist_empty(self):
        """Plan path: generateChecklist.empty"""
        result = run_script()
        assert result.returncode == 0, f"stderr: {result.stderr}"
        out = json.loads(result.stdout)
        assert out == {"todos": []}


class TestGenerateChecklistSingle:
    """Flow: generateChecklist — happy path: single item."""

    def test_generateChecklist_single(self):
        """Plan path: generateChecklist.single"""
        result = run_script("Do the thing")
        assert result.returncode == 0, f"stderr: {result.stderr}"
        out = json.loads(result.stdout)
        assert "todos" in out
        assert len(out["todos"]) == 1
        assert out["todos"][0] == {"id": "1", "content": "Do the thing", "status": "pending"}


class TestGenerateChecklistSpecialChars:
    """Flow: generateChecklist — edge case: special characters in items."""

    def test_generateChecklist_special_chars(self):
        """Plan path: generateChecklist.special-chars"""
        # Item with double-quotes and spaces
        item = 'Say "hello world"'
        result = run_script(item)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        out = json.loads(result.stdout)
        assert len(out["todos"]) == 1
        # Content must be preserved verbatim
        assert out["todos"][0]["content"] == item


# ---------------------------------------------------------------------------
# preHookInjectsChecklist tests
# ---------------------------------------------------------------------------


class TestPreHookInjectsChecklistKnownAgent:
    """Flow: preHookInjectsChecklist — known agent gets checklist prepended."""

    def test_preHookInjectsChecklist_known_agent(self):
        """Plan path: preHookInjectsChecklist.known-agent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a minimal brain.json so the hook doesn't exit early
            brain = {
                "taskDescription": "test", "taskName": "test",
                "workDir": tmpdir, "projectDir": tmpdir,
                "classification": "feature", "planFilePath": None,
                "bugFiles": None, "prUrl": None, "docsWritten": None,
                "skillsWritten": None,
                "phases": {
                    "prep-running": False, "prep-complete": True,
                    "worker-running": False, "worker-complete": False,
                    "review-running": False, "review-complete": False,
                    "docs-running": False, "docs-complete": False,
                    "skills-running": False, "skills-complete": False,
                    "pr-running": False, "pr-complete": False,
                    "cleanup-running": False, "cleanup-complete": False,
                },
            }
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "subagent_type": "feature-agent",
                    "prompt": "original prompt",
                },
            }
            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            prompt = out["tool_input"]["prompt"]
            # Prompt must be prepended with a TodoWrite instruction containing checklist JSON
            assert "TodoWrite" in prompt
            assert "Plan feature" in prompt or "todos" in prompt


class TestPreHookInjectsChecklistUnknownAgent:
    """Flow: preHookInjectsChecklist — unknown agent: prompt passes through unchanged (only brain injected)."""

    def test_preHookInjectsChecklist_unknown_agent(self):
        """Plan path: preHookInjectsChecklist.unknown-agent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = {
                "taskDescription": "test", "taskName": "test",
                "workDir": tmpdir, "projectDir": tmpdir,
                "classification": "feature", "planFilePath": None,
                "bugFiles": None, "prUrl": None, "docsWritten": None,
                "skillsWritten": None,
                "phases": {
                    "prep-running": False, "prep-complete": True,
                    "worker-running": False, "worker-complete": False,
                    "review-running": False, "review-complete": False,
                    "docs-running": False, "docs-complete": False,
                    "skills-running": False, "skills-complete": False,
                    "pr-running": False, "pr-complete": False,
                    "cleanup-running": False, "cleanup-complete": False,
                },
            }
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "subagent_type": "unknown-custom-agent",
                    "prompt": "original prompt",
                },
            }
            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            prompt = out["tool_input"]["prompt"]
            # Brain state injected, but no TodoWrite checklist
            assert "TodoWrite" not in prompt
            assert "todos" not in prompt


class TestPreHookInjectsChecklistNoBrain:
    """Flow: preHookInjectsChecklist — no DARK_FACTORY_WORK_DIR: stdin passed through unchanged."""

    def test_preHookInjectsChecklist_no_brain(self):
        """Plan path: preHookInjectsChecklist.no-brain"""
        env = dict(os.environ)
        env.pop("DARK_FACTORY_WORK_DIR", None)

        hook_input = {
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "feature-agent",
                "prompt": "original prompt",
            },
        }
        result = subprocess.run(
            ["bash", PRE_HOOK],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, f"stderr: {result.stderr}"
        out = json.loads(result.stdout)
        # No checklist injection when no brain
        assert "TodoWrite" not in json.dumps(out)


class TestPreHookInjectsChecklistNonAgentTool:
    """Flow: preHookInjectsChecklist — non-Agent tool: no checklist injection."""

    def test_preHookInjectsChecklist_non_agent_tool(self):
        """Plan path: preHookInjectsChecklist.non-agent-tool"""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = {
                "taskDescription": "test", "taskName": "test",
                "workDir": tmpdir, "projectDir": tmpdir,
                "classification": "feature", "planFilePath": None,
                "bugFiles": None, "prUrl": None, "docsWritten": None,
                "skillsWritten": None,
                "phases": {
                    "prep-running": False, "prep-complete": True,
                    "worker-running": False, "worker-complete": False,
                    "review-running": False, "review-complete": False,
                    "docs-running": False, "docs-complete": False,
                    "skills-running": False, "skills-complete": False,
                    "pr-running": False, "pr-complete": False,
                    "cleanup-running": False, "cleanup-complete": False,
                },
            }
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Bash",
                "tool_input": {"command": "ls"},
                "prompt": "run ls",
            }
            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            # No checklist in output for non-Agent tools
            assert "TodoWrite" not in json.dumps(out)
