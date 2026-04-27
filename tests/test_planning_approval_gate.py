"""
Regression test: the planning approval gate must live in feature-agent, not planning-agent.

Claude Code does not surface AskUserQuestion from 3rd-level nested sub-agents to the human user.
planning-agent runs at depth 3 (dark-factory-agent → feature-agent → planning-agent), so any
AskUserQuestion calls inside planning-agent are answered by the parent agent (feature-agent),
not by the human.

feature-agent runs at depth 2 (dark-factory-agent → feature-agent), so its AskUserQuestion
calls DO reach the human user.

This test enforces:
1. feature-agent.md contains AskUserQuestion calls for Mermaid diagram approval.
2. feature-agent.md contains AskUserQuestion calls for flow-section approval.
3. planning-agent.md does NOT contain AskUserQuestion calls (it is a pure delegator).

See: docs/bugs/2026-04-27-planning-approval-gate-bypassed.md

Flow: planningApprovalGate
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FEATURE_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "featurework", "agents", "feature-agent.md"
)
PLANNING_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "featurework", "planning", "agents", "planning-agent.md"
)


def _body(path: str) -> str:
    """Return the body of an agent file (everything after the closing front-matter ---)."""
    with open(path) as f:
        content = f.read()
    # Find the closing --- of the front-matter block (skip the opening ---)
    fm_end = content.find("\n---", 4)
    return content[fm_end + 4:] if fm_end != -1 else content


class TestPlanningApprovalGateOwnership:
    """Flow: planningApprovalGate — AskUserQuestion for plan sections must be in feature-agent"""

    def test_feature_agent_asks_user_for_mermaid_approval(self):
        """
        planningApprovalGate.mermaid: feature-agent.md must contain AskUserQuestion
        and must mention mermaid (diagram review) in its body.

        If this test fails: the mermaid approval prompt has been removed from feature-agent
        or moved back into planning-agent where it cannot reach the user.
        # Plan path: planningApprovalGate.mermaid
        """
        body = _body(FEATURE_AGENT_PATH)
        assert "AskUserQuestion" in body, (
            "feature-agent.md body must contain AskUserQuestion "
            "(approval gate must live here, not in planning-agent)"
        )
        # Must mention diagram or mermaid so the user sees it
        assert re.search(r"(?i)mermaid|diagram", body), (
            "feature-agent.md must present the Mermaid diagram section to the user "
            "via AskUserQuestion. The mermaid review is missing from feature-agent."
        )

    def test_feature_agent_asks_user_for_flow_approval(self):
        """
        planningApprovalGate.flows: feature-agent.md must present individual flow sections
        to the user via AskUserQuestion.

        If this test fails: per-flow approval has been removed from feature-agent or moved
        back into planning-agent where it cannot reach the user.
        # Plan path: planningApprovalGate.flows
        """
        body = _body(FEATURE_AGENT_PATH)
        # Must mention per-flow review (look for "flow" in the context of AskUserQuestion or review)
        assert re.search(r"(?i)flow.*review|review.*flow|flow.*approval|flow.*AskUserQuestion|AskUserQuestion.*flow", body), (
            "feature-agent.md must present each flow section to the user via AskUserQuestion. "
            "Per-flow approval is missing from feature-agent."
        )

    def test_planning_agent_does_not_ask_user_questions(self):
        """
        planningApprovalGate.no-user-questions-in-planning-agent: planning-agent.md must NOT
        declare AskUserQuestion in its front-matter tools: field.

        AskUserQuestion inside planning-agent (depth 3) is answered by the parent agent
        (feature-agent), not the human user. If planning-agent declares AskUserQuestion in
        tools: and calls it, the approval gate is silently bypassed.

        We check the tools: front-matter (not just the body text) because planning-agent.md
        may legitimately mention AskUserQuestion in explanatory prose about why it is excluded.
        # Plan path: planningApprovalGate.no-user-questions-in-planning-agent
        """
        with open(PLANNING_AGENT_PATH) as f:
            content = f.read()

        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, "planning-agent.md must have YAML front-matter"
        front_matter = fm_match.group(1)

        tools_match = re.search(r"^tools:\s*(.+)$", front_matter, re.MULTILINE)
        if not tools_match:
            # No tools: field at all — AskUserQuestion definitely not declared
            return

        tools = [t.strip() for t in tools_match.group(1).split(",")]
        assert "AskUserQuestion" not in tools, (
            "planning-agent.md front-matter tools: must NOT include AskUserQuestion. "
            "planning-agent runs at depth 3 (dark-factory-agent → feature-agent → planning-agent) "
            "and AskUserQuestion in a sub-agent at that depth is answered by the parent agent, "
            "not the human user. Move all approval prompts to feature-agent."
        )

        # Secondary guard: the agent body must not contain an affirmative imperative call
        # instruction for AskUserQuestion. We look for lines where "AskUserQuestion" appears
        # without a preceding negation keyword (never, not, no, don't, do not) on the same line.
        # This allows explanatory prose like "Never use AskUserQuestion" or
        # "You do not use AskUserQuestion" while catching "Use AskUserQuestion to confirm...".
        body = _body(PLANNING_AGENT_PATH)
        for line in body.splitlines():
            if "AskUserQuestion" not in line:
                continue
            # Skip lines that are negation prose
            if re.search(r"(?i)(never|not|no\b|don't|do not)\s+(use|call|invoke)\s+AskUserQuestion", line):
                continue
            # Flag any remaining line that contains an affirmative call pattern
            if re.search(r"(?i)(use|call|invoke)\s+AskUserQuestion", line):
                raise AssertionError(
                    f"planning-agent.md body contains an affirmative AskUserQuestion call "
                    f"instruction: {line!r}. All user interaction must remain in feature-agent."
                )

    def test_feature_agent_declares_ask_user_question_in_tools(self):
        """
        planningApprovalGate.tools-declared: feature-agent.md must declare AskUserQuestion
        in its YAML front-matter tools: field.

        Without this declaration, Claude Code will not grant the tool at runtime.
        # Plan path: planningApprovalGate.tools-declared
        """
        with open(FEATURE_AGENT_PATH) as f:
            content = f.read()

        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, "feature-agent.md must have YAML front-matter"
        front_matter = fm_match.group(1)

        tools_match = re.search(r"^tools:\s*(.+)$", front_matter, re.MULTILINE)
        assert tools_match, "feature-agent.md must have a tools: field in front-matter"
        tools = [t.strip() for t in tools_match.group(1).split(",")]

        assert "AskUserQuestion" in tools, (
            f"feature-agent.md front-matter tools: must include AskUserQuestion. "
            f"Current tools: {tools}"
        )

    def test_feature_agent_has_final_plan_approval_gate(self):
        """
        planningApprovalGate.final-approval: feature-agent.md must contain a final full-plan
        AskUserQuestion gate (Phase 4) with an Abort option.

        The fix moves per-section approvals into feature-agent, but the final full-plan
        confirmation (and its Abort path) are also safety-critical. If this gate is
        removed, execution can proceed without a final human sign-off.
        # Plan path: planningApprovalGate.final-approval
        """
        body = _body(FEATURE_AGENT_PATH)
        # The final approval AskUserQuestion must be present
        assert re.search(r"(?i)final.*approval|approval.*final|final.*plan.*approval", body), (
            "feature-agent.md must contain a final full-plan approval step (Phase 4). "
            "The final AskUserQuestion gate before execution is missing."
        )
        # The Abort option must be present so the user can cancel
        assert re.search(r"(?i)\bAbort\b", body), (
            "feature-agent.md must offer an Abort option in the final plan approval gate. "
            "Without it, the user cannot cancel feature work at the final review step."
        )
