"""
Regression tests for manufacture stop patterns (bug: 2026-05-08-manufacture-stops-mid-orchestration).

Two observed stop patterns:
- Pattern 1 (Feature route): Agent calls build-factory.sh instead of prep-feature-dir.sh, then stops.
- Pattern 2 (Repair route): Agent stops after Steps 1-3 instead of continuing to Step 4.

Root causes:
1. dark-factory-agent has a multi-turn loop with status=='question' for feature-agent.
   Feature-agent runs at depth 2 and can call AskUserQuestion directly; this loop is unnecessary,
   fragile, and causes Haiku to lose execution context.
2. feature-agent contradicts itself: AskUserQuestion in tools: but Rules say never call it.
3. Non-Stop Execution prose is at the bottom of the file — Haiku may not read it before starting.

See: docs/bugs/2026-05-08-manufacture-stops-mid-orchestration.md

Flow: manufactureStopPatterns
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DARK_FACTORY_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "dark-factory", "agents", "dark-factory-agent.md"
)
FEATURE_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "featurework", "agents", "feature-agent.md"
)


def _body(path: str) -> str:
    """Return the body of an agent/skill file (everything after the closing front-matter ---)."""
    with open(path) as f:
        content = f.read()
    fm_end = content.find("\n---", 4)
    return content[fm_end + 4:] if fm_end != -1 else content


def _full(path: str) -> str:
    """Return the full file content."""
    with open(path) as f:
        return f.read()


def _frontmatter(path: str) -> str:
    """Return only the YAML frontmatter block of a file."""
    with open(path) as f:
        content = f.read()
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    return match.group(1) if match else ""


# ---------------------------------------------------------------------------
# Pattern 1 — dark-factory-agent must NOT implement multi-turn loop for feature-agent
# ---------------------------------------------------------------------------

class TestNoMultiTurnLoop:
    """
    manufactureStopPatterns — dark-factory-agent must not implement a multi-turn loop
    with status=='question' for feature-agent. Feature-agent runs at depth 2 and can
    call AskUserQuestion directly, eliminating the need for the loop.
    """

    def test_dark_factory_agent_has_no_status_question_loop(self):
        """
        manufactureStopPatterns.no-status-question-loop: dark-factory-agent.md must NOT
        contain a multi-turn loop that checks `status == "question"` for feature-agent
        responses.

        This loop is the primary cause of Pattern 1 (feature route calls build-factory.sh):
        Haiku loses execution context while navigating the loop and calls the wrong action.
        Feature-agent runs at depth 2 (dark-factory-agent → feature-agent), so it CAN call
        AskUserQuestion directly. No loop is needed — dark-factory-agent invokes feature-agent
        once and waits for status: done/hard-stop/aborted.

        If this test fails: dark-factory-agent.md still has `status == "question"` loop logic
        that confuses Haiku and causes mid-orchestration stops.
        # Plan path: manufactureStopPatterns.no-status-question-loop
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        assert not re.search(
            r'(?i)status.*==.*["\']question["\']|["\']question["\'].*==.*status',
            body,
        ), (
            "dark-factory-agent.md must NOT implement a multi-turn loop checking "
            "status == 'question' for feature-agent responses. Feature-agent runs at depth 2 "
            "and can call AskUserQuestion directly. Remove the multi-turn loop — invoke "
            "feature-agent once and wait for status: done/hard-stop/aborted."
        )

    def test_dark_factory_agent_feature_route_invokes_once(self):
        """
        manufactureStopPatterns.feature-invoke-once: dark-factory-agent.md feature route
        must invoke feature-agent as a single call (not wrapped in a LOOP/CONTINUE block
        that re-invokes with answer/planPath parameters).

        When dark-factory-agent loops over feature-agent with question/answer protocol,
        Haiku loses context and confuses setup steps (calls build-factory.sh instead of
        prep-feature-dir.sh).

        If this test fails: the feature-agent invocation is wrapped in a loop that re-invokes
        feature-agent with `answer` and `planPath` — this loop must be removed.
        # Plan path: manufactureStopPatterns.feature-invoke-once
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Look for pattern: feature-agent invocation with answer parameter on re-invocation
        # This is the signal that a multi-turn loop exists
        assert not re.search(
            r'(?i)invoke feature-agent.*answer.*planPath.*CONTINUE|CONTINUE LOOP.*feature-agent',
            body,
        ), (
            "dark-factory-agent.md must NOT re-invoke feature-agent with answer/planPath "
            "parameters in a CONTINUE LOOP pattern. Invoke feature-agent once and wait for "
            "status: done/hard-stop/aborted. Feature-agent handles all user interaction via "
            "AskUserQuestion directly."
        )


# ---------------------------------------------------------------------------
# Pattern 1 — feature-agent must use AskUserQuestion directly
# ---------------------------------------------------------------------------

class TestFeatureAgentDirectAskUserQuestion:
    """
    manufactureStopPatterns — feature-agent must use AskUserQuestion directly for all
    user interaction, not return status:'question' to dark-factory-agent.
    """

    def test_feature_agent_rules_say_call_askuserquestion(self):
        """
        manufactureStopPatterns.feature-agent-call-askuserquestion: feature-agent.md Rules
        section must NOT say "Never call AskUserQuestion". The correct rule is that
        feature-agent DOES call AskUserQuestion directly (since it runs at depth 2).

        If this test fails: feature-agent.md still has the contradictory rule "Never call
        AskUserQuestion", causing Haiku to return status:'question' instead of prompting
        the user directly.
        # Plan path: manufactureStopPatterns.feature-agent-call-askuserquestion
        """
        body = _body(FEATURE_AGENT_PATH)
        # The Rules section must NOT contain "Never call AskUserQuestion" or equivalent prohibition
        assert not re.search(
            r'(?i)never\s+call\s+AskUserQuestion|do\s+not\s+call\s+AskUserQuestion',
            body,
        ), (
            "feature-agent.md Rules must NOT say 'Never call AskUserQuestion'. "
            "Feature-agent runs at depth 2 and must call AskUserQuestion directly for all "
            "user interaction (mermaid approval, flow approval, final approval). "
            "Remove the prohibition and update the orchestration pseudocode to call "
            "AskUserQuestion inline instead of returning status:'question'."
        )

    def test_feature_agent_pseudocode_calls_askuserquestion_for_mermaid(self):
        """
        manufactureStopPatterns.feature-agent-mermaid-ask: feature-agent.md orchestration
        pseudocode must contain an AskUserQuestion call for the mermaid diagram phase.

        If this test fails: the mermaid approval step uses RETURN status:'question'
        instead of calling AskUserQuestion directly.
        # Plan path: manufactureStopPatterns.feature-agent-mermaid-ask
        """
        body = _body(FEATURE_AGENT_PATH)
        # Look for AskUserQuestion near "mermaid" in the pseudocode
        assert re.search(
            r'(?i)(AskUserQuestion[^\n]*mermaid|mermaid[^\n]*AskUserQuestion)',
            body,
        ), (
            "feature-agent.md orchestration pseudocode must call AskUserQuestion for mermaid "
            "diagram approval. Currently it uses RETURN status:'question' which requires "
            "dark-factory-agent to implement a fragile multi-turn loop."
        )

    def test_feature_agent_pseudocode_has_no_return_status_question(self):
        """
        manufactureStopPatterns.feature-agent-no-return-question: feature-agent.md
        orchestration pseudocode must NOT contain `RETURN { status: "question" }` or
        equivalent return-question protocol.

        If this test fails: feature-agent still uses the return-question protocol,
        requiring dark-factory-agent to implement the multi-turn loop.
        # Plan path: manufactureStopPatterns.feature-agent-no-return-question
        """
        body = _body(FEATURE_AGENT_PATH)
        # Extract only the orchestration pseudocode block
        code_block = re.search(r"```\n(.*?)\n```", body, re.DOTALL)
        if not code_block:
            return  # No code block — test cannot confirm
        code = code_block.group(1)
        # Look for RETURN with status:question pattern
        assert not re.search(
            r'(?i)RETURN\s*\{[^}]*status.*["\']question["\']',
            code,
        ), (
            "feature-agent.md orchestration pseudocode must NOT contain "
            "`RETURN { status: 'question' }`. Feature-agent must call AskUserQuestion "
            "directly for all user interaction — dark-factory-agent must not need to loop."
        )


# ---------------------------------------------------------------------------
# Pattern 2 — Non-Stop Execution enforcement must be at the top of instructions
# ---------------------------------------------------------------------------

class TestNonStopExecutionPlacement:
    """
    manufactureStopPatterns — the Non-Stop Execution block must appear near the TOP
    of dark-factory-agent's instructions so Haiku reads it before starting any step.
    """

    def test_non_stop_block_appears_before_step_4(self):
        """
        manufactureStopPatterns.non-stop-before-step4: dark-factory-agent.md must contain
        the Non-Stop Execution / CRITICAL stop prohibition BEFORE the Step 4 worker routing
        section, so Haiku encounters it before making routing decisions.

        If this test fails: the Non-Stop Execution block is at the bottom of the file
        (after the orchestration pseudocode), meaning Haiku may not read it before executing.
        # Plan path: manufactureStopPatterns.non-stop-before-step4
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        non_stop_pos = body.find("Non-Stop Execution")
        if non_stop_pos == -1:
            # Try alternate phrasing
            non_stop_pos = body.find("CRITICAL")
            if non_stop_pos == -1:
                pytest.fail(
                    "dark-factory-agent.md body must contain a Non-Stop Execution or CRITICAL "
                    "enforcement block. This block tells Haiku not to stop between steps."
                )

        # Find position of "Step 4" in the body
        step4_pos = body.find("# Step 4")
        if step4_pos == -1:
            step4_pos = body.find("Step 4")

        if step4_pos == -1:
            return  # Can't find Step 4 — skip positional check

        assert non_stop_pos < step4_pos, (
            "dark-factory-agent.md Non-Stop Execution / CRITICAL block must appear BEFORE "
            "the Step 4 section. Currently it is after Step 4, meaning Haiku may not read it "
            "before making routing decisions. Move the block to the top of the orchestration "
            "pseudocode (before Step 1) or as a header comment."
        )
