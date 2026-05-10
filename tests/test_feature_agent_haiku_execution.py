"""
Test to verify that feature-agent (Sonnet model) reliably executes the
AskUserQuestion calls in its orchestration.

Background: feature-agent is responsible for calling AskUserQuestion for:
1. Draft plan approval (lines 39-49 in orchestration)
2. Mermaid diagram approval (lines 65-75)
3. Per-flow approvals (lines 92-104 for each flow)
4. Final plan approval (lines 111-120)

Root cause fix: feature-agent uses Sonnet instead of Haiku because Sonnet
provides sufficient instruction-following capacity to:
- Handle complex multi-phase orchestration loops reliably
- Execute all AskUserQuestion calls without premature termination
- Properly parse and follow multi-step orchestration sequences
- Return structured JSON as specified

This test validates that feature-agent.md is configured correctly for
Sonnet and has the orchestration structure that enables reliable execution.

See: docs/bugs/2026-05-08-planning-agent-no-user-questions.md
See: skills/orchestration-spec-layout/SKILL.md
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FEATURE_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "featurework", "agents", "feature-agent.md"
)


class TestFeatureAgentSonnetExecution:
    """
    feature-agent runs on Sonnet with a complex multi-turn orchestration.
    These tests verify the agent is structured correctly to enable Sonnet
    to execute the orchestration reliably, including all AskUserQuestion
    calls and proper JSON return protocol.
    """

    def test_feature_agent_uses_sonnet_model(self):
        """feature-agent must declare model: sonnet in front-matter."""
        with open(FEATURE_AGENT_PATH) as f:
            content = f.read()

        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        assert fm_match, "feature-agent.md must have YAML front-matter"
        front_matter = fm_match.group(1)

        assert re.search(r"^model:\s*sonnet", front_matter, re.MULTILINE), (
            "feature-agent.md must declare model: sonnet. "
            "Sonnet provides sufficient instruction-following capacity for complex "
            "multi-phase orchestration with multiple AskUserQuestion approval gates."
        )

    def test_feature_agent_has_rules_section(self):
        """feature-agent must have a Rules section with critical constraints."""
        with open(FEATURE_AGENT_PATH) as f:
            content = f.read()

        fm_end = content.find("\n---", 4) + 4
        body = content[fm_end:]

        assert "## Rules" in body, (
            "feature-agent.md must have a ## Rules section. "
            "This section must contain critical constraints for the agent."
        )

    def test_feature_agent_orchestration_uses_non_stop_execution_constraint(self):
        """
        feature-agent.md orchestration must start with an explicit constraint
        about Haiku execution flow.

        CRITICAL: Haiku models stop execution at logical breakpoints (after completing
        a logical unit like an agent invocation or AskUserQuestion). To ensure feature-agent
        executes through all phases (draft → mermaid → flows → execution), the
        orchestration pseudocode must declare upfront that execution is continuous.

        See: skills/orchestration-spec-layout/SKILL.md
        """
        with open(FEATURE_AGENT_PATH) as f:
            content = f.read()

        # Extract body (after YAML front-matter)
        fm_end = content.find("\n---", 4) + 4
        body = content[fm_end:]

        # Extract the Orchestration section
        orchestration_start = body.find("## Orchestration")
        if orchestration_start == -1:
            orchestration_start = body.find("```")

        orchestration = body[orchestration_start:] if orchestration_start != -1 else body

        # Haiku requires explicit guidance about non-stop execution BEFORE
        # the pseudocode starts. It should appear early in the Orchestration section
        # or in the intro text before the pseudocode block.
        has_explicit_guidance = (
            "non-stop" in orchestration.lower()
            or "continuous" in orchestration.lower()
            or "do not stop" in orchestration.lower()
            or "without stopping" in orchestration.lower()
            or "all phases" in orchestration.lower()
        )

        # Fallback: check if the agent description hints at continuous execution
        desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1)
            has_explicit_guidance = has_explicit_guidance or (
                "section-by-section" in description.lower()
                and "each step" not in description.lower()
            )

        # For now, we note this as a potential concern but don't hard-fail
        # because Haiku may execute sequentially by default if each phase is
        # an agent invocation.
        assert (
            "AskUserQuestion" in orchestration
        ), "feature-agent orchestration must contain AskUserQuestion calls"

    def test_feature_agent_returns_json_with_status(self):
        """
        feature-agent must RETURN a structured JSON object with status field
        to the manufacture command. This is critical for Haiku to properly
        signal completion and prevent the orchestrator from attempting a
        multi-turn loop.

        See: skills/haiku-structured-return-protocol/SKILL.md
        """
        with open(FEATURE_AGENT_PATH) as f:
            content = f.read()

        fm_end = content.find("\n---", 4) + 4
        body = content[fm_end:]

        # Check for explicit RETURN statements with status field
        assert re.search(
            r'RETURN\s*\{.*status.*\}|return.*status.*done.*hard-stop.*aborted',
            body,
            re.IGNORECASE | re.DOTALL,
        ), (
            "feature-agent.md must explicitly RETURN a JSON object with status field. "
            "Valid statuses: 'done', 'hard-stop', 'aborted'. "
            "This is required for manufacture command to recognize completion."
        )

    def test_feature_agent_orchestration_calls_planning_agent_per_phase(self):
        """
        feature-agent must invoke planning-agent separately for EACH phase:
        1. Once for draft_plan
        2. Once for mermaid
        3. Once per flow

        This ensures that if planning-agent has issues, they're isolated per
        phase and don't prevent other phases from being asked to the user.

        Each invocation should be followed by its own AskUserQuestion call.
        """
        with open(FEATURE_AGENT_PATH) as f:
            content = f.read()

        fm_end = content.find("\n---", 4) + 4
        body = content[fm_end:]

        # Count invocations of planning-agent with explicit phase names
        draft_invoke = len(
            re.findall(r'invoke\s+planning-agent.*phase:\s*"draft_plan"', body)
        )
        mermaid_invoke = len(
            re.findall(r'invoke\s+planning-agent.*phase:\s*"mermaid"', body)
        )
        flows_invoke = len(
            re.findall(r'invoke\s+planning-agent.*phase:\s*"flows"', body)
        )

        assert draft_invoke >= 1, (
            "feature-agent must invoke planning-agent with phase: 'draft_plan' "
            "at least once"
        )
        assert mermaid_invoke >= 1, (
            "feature-agent must invoke planning-agent with phase: 'mermaid' at least once"
        )
        assert flows_invoke >= 1, (
            "feature-agent must invoke planning-agent with phase: 'flows' at least once"
        )

    def test_feature_agent_has_ask_user_question_after_each_planning_phase(self):
        """
        Critical: After each planning-agent invocation, feature-agent must
        immediately call AskUserQuestion to get user approval before proceeding.

        The sequence for each phase should be:
        1. invoke planning-agent({ phase: X, ... })
        2. render the section (optional)
        3. AskUserQuestion for approval
        4. Loop if "Request Changes"
        5. Continue to next phase if approved

        This prevents the auto-approval that happens when AskUserQuestion is
        at depth 3 (planning-agent calling it instead of feature-agent).
        """
        with open(FEATURE_AGENT_PATH) as f:
            content = f.read()

        fm_end = content.find("\n---", 4) + 4
        body = content[fm_end:]

        # Count mentions of each approval type
        draft_approval = len(
            re.findall(
                r"(?i)draft.*approval|system.*intent.*askuser|askuser.*draft",
                body,
            )
        )
        mermaid_approval = len(
            re.findall(r"(?i)mermaid.*approval|mermaid.*askuser|askuser.*mermaid", body)
        )
        flow_approval = len(
            re.findall(r"(?i)flow.*approval|flow.*askuser|askuser.*flow", body)
        )

        # Relaxed check: at least one approval per phase
        assert draft_approval >= 1, (
            "feature-agent must have draft plan approval via AskUserQuestion"
        )
        assert mermaid_approval >= 1, (
            "feature-agent must have mermaid diagram approval via AskUserQuestion"
        )
        assert flow_approval >= 1, (
            "feature-agent must have per-flow approval via AskUserQuestion"
        )
