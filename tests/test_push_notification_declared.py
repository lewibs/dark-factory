"""
Regression test: every agent that calls PushNotification in its body
must also declare PushNotification in its YAML front-matter tools: field.

If an agent is missing PushNotification from tools:, the Claude Code runtime
will not grant access to the tool and the notification will silently be skipped.
"""

import os
import re
import pytest

# Absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agent files known to call PushNotification in their body.
# Originally 8 agents (docs/bugs/2026-04-25-push-notification-missing-from-tools.md).
# planning-agent was removed from this list because all PushNotification calls moved to
# feature-agent as part of the planning-approval-gate fix
# (docs/bugs/2026-04-27-planning-approval-gate-bypassed.md).
# planning-agent is now a pure phase-delegator with no user interaction.
AGENTS_USING_PUSH_NOTIFICATION = [
    "agents/featurework/agents/feature-agent.md",
    "agents/featurework/execution/agents/execution-agent.md",
    "agents/fix-flow/agents/fix-flow-orchestrator.md",
    "agents/fix-flow/agents/ralph-fix-and-push.md",
    "agents/dark-factory/agents/dark-factory-agent.md",
    "agents/documentation/agents/detect-drift-agent.md",
    "agents/documentation/agents/update-documentation-agent.md",
]


def parse_front_matter_tools(content: str) -> list[str]:
    """
    Extract the tools list from a YAML front-matter block.
    Returns an empty list if no front-matter or no tools: field is found.
    Front-matter is delimited by --- at start and end.
    tools: Read, Bash, Agent, PushNotification
    """
    # Match the front-matter block between --- delimiters
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        return []
    front_matter = fm_match.group(1)

    # Find the tools: line
    tools_match = re.search(r"^tools:\s*(.+)$", front_matter, re.MULTILINE)
    if not tools_match:
        return []

    # Split comma-separated tool names and strip whitespace
    tools_str = tools_match.group(1)
    return [t.strip() for t in tools_str.split(",")]


@pytest.mark.parametrize("agent_path", AGENTS_USING_PUSH_NOTIFICATION)
def test_push_notification_in_tools_field(agent_path: str) -> None:
    """
    Assert that each agent file that calls PushNotification declares it
    in the tools: front-matter field.
    """
    abs_path = os.path.join(PROJECT_ROOT, agent_path)
    assert os.path.exists(abs_path), f"Agent file not found: {abs_path}"

    with open(abs_path, "r") as f:
        content = f.read()

    # Sanity check: the agent body (after the front-matter) actually references PushNotification.
    # We strip the front-matter block so the tools: declaration itself does not satisfy this check.
    fm_end = content.find("\n---", 4)  # find closing --- of front-matter (skip opening ---)
    body = content[fm_end + 4:] if fm_end != -1 else content
    assert "PushNotification" in body, (
        f"{agent_path}: file body does not reference PushNotification "
        f"(test list may be stale or the body call was removed)"
    )

    tools = parse_front_matter_tools(content)
    assert "PushNotification" in tools, (
        f"{agent_path}: PushNotification is called in the agent body but is NOT "
        f"listed in the tools: front-matter field. "
        f"Current tools: {tools}. "
        f"Claude Code will not grant access to this tool at runtime."
    )
