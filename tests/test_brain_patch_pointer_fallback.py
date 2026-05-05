"""
Tests for brain-patch.json pointer file fallback pattern.

Verifies that each agent's brain-patch.json write instruction includes
the pointer file fallback pattern (references /tmp/dark-factory-work-dir).
"""

import os


def _read_agent_file(agent_path):
    """Helper to read an agent markdown file."""
    abs_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        agent_path
    )
    with open(abs_path, 'r') as f:
        return f.read()


def _has_pointer_fallback(content):
    """Check if content includes the pointer file fallback pattern."""
    # Check for the fallback pattern that reads from /tmp/dark-factory-work-dir
    return '/tmp/dark-factory-work-dir' in content


def test_feature_agent_has_pointer_fallback():
    """
    # Plan path: fix-feature-agent-brain-patch
    Verify feature-agent.md contains pointer file fallback in brain-patch.json write rule.
    """
    content = _read_agent_file('agents/featurework/agents/feature-agent.md')
    assert _has_pointer_fallback(content), \
        "feature-agent.md must include /tmp/dark-factory-work-dir fallback"


def test_pr_agent_has_pointer_fallback():
    """
    # Plan path: fix-pr-agent-brain-patch
    Verify pr-agent.md contains pointer file fallback in brain-patch.json write rule.
    """
    content = _read_agent_file('agents/pr/agents/pr-agent.md')
    assert _has_pointer_fallback(content), \
        "pr-agent.md must include /tmp/dark-factory-work-dir fallback"


def test_skill_update_agent_has_pointer_fallback():
    """
    # Plan path: fix-skill-update-agent-brain-patch
    Verify skill-update-agent.md contains pointer file fallback in brain-patch.json write rule.
    """
    content = _read_agent_file('agents/skill-update/agents/skill-update-agent.md')
    assert _has_pointer_fallback(content), \
        "skill-update-agent.md must include /tmp/dark-factory-work-dir fallback"


def test_update_documentation_agent_has_pointer_fallback():
    """
    # Plan path: fix-update-documentation-agent-brain-patch
    Verify update-documentation-agent.md contains pointer file fallback in brain-patch.json write rule.
    """
    content = _read_agent_file('agents/documentation/agents/update-documentation-agent.md')
    assert _has_pointer_fallback(content), \
        "update-documentation-agent.md must include /tmp/dark-factory-work-dir fallback"


def test_debugger_agent_has_pointer_fallback():
    """
    # Plan path: fix-debugger-agent-brain-patch
    Verify debugger-agent.md contains pointer file fallback in brain-patch.json write rule.
    """
    content = _read_agent_file('agents/debugger/agents/debugger-agent.md')
    assert _has_pointer_fallback(content), \
        "debugger-agent.md must include /tmp/dark-factory-work-dir fallback"
