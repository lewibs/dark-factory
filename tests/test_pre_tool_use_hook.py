"""
Tests for pre-tool-use-hook.sh AGENT_CHECKLISTS entries for planning-agent and sub-planning-agent.

Verifies that:
- sub-planning-agent checklist is injected when that agent is spawned
- planning-agent checklist reflects new orchestrator duties

Flow: orchestratorHook
"""

import json
import os
import subprocess
import tempfile

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE_HOOK = os.path.join(
    REPO_ROOT, "agents", "dark-factory", "scripts", "pre-tool-use-hook.sh"
)

ALL_PHASES_FALSE = {
    "prep-running": False,
    "prep-complete": False,
    "worker-running": False,
    "worker-complete": False,
    "review-running": False,
    "review-complete": False,
    "docs-running": False,
    "docs-complete": False,
    "skills-running": False,
    "skills-complete": False,
    "pr-running": False,
    "pr-complete": False,
    "cleanup-running": False,
    "cleanup-complete": False,
}


def make_brain(phases=None):
    base_phases = dict(ALL_PHASES_FALSE)
    if phases:
        base_phases.update(phases)
    return {
        "taskDescription": "test task",
        "taskName": "test",
        "workDir": "/tmp/test",
        "projectDir": "/tmp/project",
        "classification": "feature",
        "planFilePath": None,
        "bugFiles": None,
        "prUrl": None,
        "docsWritten": None,
        "skillsWritten": None,
        "phases": base_phases,
    }


def run_hook(tool_input: dict, env_override: dict | None = None) -> subprocess.CompletedProcess:
    """Run the pre-tool-use-hook.sh with the given tool_input JSON via stdin."""
    env = dict(os.environ)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["bash", PRE_HOOK],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
    )


class TestOrchestratorHookSubPlanningAgent:
    """Flow: orchestratorHook — sub-planning-agent checklist injection"""

    def test_sub_planning_agent_checklist_injected(self):
        """
        orchestratorHook.sub-planning-agent: when the Agent tool is invoked with
        subagent_type=sub-planning-agent, the hook injects checklist items into the prompt.
        Expected checklist items: Research phase context, Update plan file,
        Run mermaid script (mermaid phase only), Return structured output
        # Plan path: orchestratorHook.sub-planning-agent
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain()
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "subagent_type": "sub-planning-agent",
                    "prompt": "do the planning work",
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            prompt = out["tool_input"]["prompt"]

            # The hook should inject checklist items for sub-planning-agent
            assert "Research phase context" in prompt, (
                f"Expected 'Research phase context' in prompt, got: {prompt[:500]}"
            )
            assert "Update plan file" in prompt, (
                f"Expected 'Update plan file' in prompt, got: {prompt[:500]}"
            )
            assert "Run mermaid script" in prompt, (
                f"Expected 'Run mermaid script' in prompt, got: {prompt[:500]}"
            )
            assert "Return structured output" in prompt, (
                f"Expected 'Return structured output' in prompt, got: {prompt[:500]}"
            )


class TestOrchestratorHookPlanningAgent:
    """Flow: orchestratorHook — planning-agent checklist updated to reflect orchestrator duties"""

    def test_planning_agent_checklist_updated(self):
        """
        orchestratorHook.planning-agent: when the Agent tool is invoked with
        subagent_type=planning-agent, the hook injects the updated orchestrator checklist.
        Expected items: Spawn draft-plan sub-agent, Run mermaid phase,
        Run flows phase (one at a time), Return planPath
        # Plan path: orchestratorHook.planning-agent
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = make_brain()
            brain_path = os.path.join(tmpdir, "brain.json")
            with open(brain_path, "w") as f:
                json.dump(brain, f)

            hook_input = {
                "tool_name": "Agent",
                "tool_input": {
                    "subagent_type": "planning-agent",
                    "prompt": "plan the feature",
                },
            }

            result = run_hook(hook_input, env_override={"DARK_FACTORY_WORK_DIR": tmpdir})

            assert result.returncode == 0, f"stderr: {result.stderr}"
            out = json.loads(result.stdout)
            prompt = out["tool_input"]["prompt"]

            # The hook should inject the new orchestrator checklist for planning-agent
            assert "Spawn draft-plan sub-agent" in prompt, (
                f"Expected 'Spawn draft-plan sub-agent' in prompt, got: {prompt[:500]}"
            )
            assert "Run mermaid phase" in prompt, (
                f"Expected 'Run mermaid phase' in prompt, got: {prompt[:500]}"
            )
            assert "Run flows phase" in prompt, (
                f"Expected 'Run flows phase' in prompt, got: {prompt[:500]}"
            )
            assert "Return planPath" in prompt, (
                f"Expected 'Return planPath' in prompt, got: {prompt[:500]}"
            )
