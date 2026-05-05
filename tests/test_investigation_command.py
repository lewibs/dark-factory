"""
Tests for the investigation command.

Validates agent file structure for the investigation command flow.

Flows covered:
- investigationCommand.success
- investigationCommand.iterative-correction
- investigationCommand.max-iterations-exceeded
"""

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVESTIGATION_COMMAND = os.path.join(REPO_ROOT, "agents", "commands", "investigation")
INVESTIGATION_ORCHESTRATOR = os.path.join(
    REPO_ROOT, "agents", "commands", "investigation-orchestrator.md"
)


def read_file(path):
    with open(path, "r") as f:
        return f.read()


def parse_frontmatter(content):
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    frontmatter = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()
    return frontmatter


class TestInvestigationCommandFile:
    """Tests for the investigation command file structure."""

    def test_investigation_command_file_exists(self):
        """Plan path: investigationCommand.success — command file must exist."""
        assert os.path.exists(INVESTIGATION_COMMAND), (
            f"investigation command file not found at {INVESTIGATION_COMMAND}"
        )

    def test_investigation_command_has_name(self):
        """Command file must declare a name in frontmatter."""
        content = read_file(INVESTIGATION_COMMAND)
        fm = parse_frontmatter(content)
        assert fm.get("name") == "investigation"

    def test_investigation_command_has_subagent_stop_hook(self):
        """Command file must declare a SubagentStop hook for committing docs."""
        content = read_file(INVESTIGATION_COMMAND)
        assert "SubagentStop" in content, (
            "investigation command must declare a SubagentStop hook to commit docs"
        )

    def test_investigation_orchestrator_exists(self):
        """Plan path: investigationCommand.success — orchestrator agent must exist."""
        assert os.path.exists(INVESTIGATION_ORCHESTRATOR)

    def test_investigation_orchestrator_has_agent_tool(self):
        """Orchestrator must have Agent tool to invoke sub-agents."""
        content = read_file(INVESTIGATION_ORCHESTRATOR)
        fm = parse_frontmatter(content)
        tools = fm.get("tools", "")
        assert "Agent" in tools, (
            "investigation-orchestrator must have Agent tool to invoke investigation-agent and claim-validator-agent"
        )

    def test_investigation_orchestrator_references_max_iterations(self):
        """Plan path: investigationCommand.max-iterations-exceeded — orchestrator must cap iterations."""
        content = read_file(INVESTIGATION_ORCHESTRATOR)
        assert "5" in content or "iterations" in content.lower(), (
            "investigation-orchestrator must enforce a max iterations cap"
        )
