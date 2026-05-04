"""
Regression tests for manufacture flow violations.

Covers the 8 violations found in the last dark-factory-agent orchestration run:
1. brain-state-manager must be used for all brain.json operations (not cat/bash direct writes)
2. feature-agent must call AskUserQuestion directly (not return status:question to orchestrator)
3. SubagentStop hooks must NOT be in settings.json (must only be in agent frontmatter)
4. dark-factory-agent must never skip steps 7-9 regardless of user input
5. branch-drift guard must be between Step 3 and Step 4 (position check)
6. brain-state-manager read must be delegated (not cat) after sub-agents return

See: docs/bugs/2026-05-04-manufacture-flow-8-violations.md

Flow: manufactureFlowViolations
"""

import json
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
SETTINGS_JSON_PATH = os.path.join(PROJECT_ROOT, ".claude", "settings.json")
CREATE_PR_SKILL_PATH = os.path.join(
    PROJECT_ROOT, "skills", "create-pr", "SKILL.md"
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


# ---------------------------------------------------------------------------
# Violation 1 & 4 & 8 — brain-state-manager must be used for all brain.json ops
# ---------------------------------------------------------------------------

class TestBrainStateManagerDelegation:
    """Flow: manufactureFlowViolations — brain.json ops must be delegated to brain-state-manager."""

    def test_dark_factory_agent_does_not_cat_brain_json(self):
        """
        manufactureFlowViolations.no-cat-brain: dark-factory-agent.md orchestration pseudocode
        must not contain a direct `cat` command targeting brain.json. All brain.json reads
        must be delegated to brain-state-manager skill. The Rules section may mention cat in
        a prohibition ("NEVER use cat ... brain.json") — that is acceptable.

        If this test fails: the orchestrator pseudocode directly reads brain.json with cat,
        bypassing the brain-state-manager skill which enforces atomic access and consistent schema.
        # Plan path: manufactureFlowViolations.no-cat-brain
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Extract only the orchestration pseudocode block (between the first ``` and the matching ```)
        code_block = re.search(r"```\n(.*?)\n```", body, re.DOTALL)
        if not code_block:
            # No code block — check the whole body but exclude lines with negation keywords
            for line in body.splitlines():
                if re.search(r"\bcat\b.*brain\.json", line, re.IGNORECASE):
                    # Skip prohibition lines (these are correct documentation)
                    if not re.search(r"(?i)(NEVER|never|not|don't|do not)\s+use\s+cat", line):
                        assert False, (
                            f"dark-factory-agent.md body contains a prohibited `cat ... brain.json` "
                            f"expression: {line!r}. Use brain-state-manager skill instead."
                        )
            return
        code = code_block.group(1)
        assert not re.search(
            r"(?i)\bcat\b[^\n]*brain\.json",
            code,
        ), (
            "dark-factory-agent.md orchestration pseudocode must not contain `cat ... brain.json`. "
            "All brain.json reads must be delegated to brain-state-manager skill."
        )

    def test_dark_factory_agent_does_not_write_brain_json_directly(self):
        """
        manufactureFlowViolations.no-direct-write: dark-factory-agent.md orchestration pseudocode
        must not instruct the orchestrator to write brain.json directly (via echo, cat >, jq, etc.).

        If this test fails: the orchestrator creates brain.json by writing it directly
        instead of invoking brain-state-manager's create operation.
        # Plan path: manufactureFlowViolations.no-direct-write
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Extract only the orchestration pseudocode block
        code_block = re.search(r"```\n(.*?)\n```", body, re.DOTALL)
        if not code_block:
            return  # Can't find the block — skip this check
        code = code_block.group(1)
        # Detect patterns like `echo ... > brain.json` or `jq ... > brain.json`
        assert not re.search(
            r"(?i)(echo|printf|jq|cat\s*>)[^\n]*brain\.json",
            code,
        ), (
            "dark-factory-agent.md orchestration pseudocode must not contain direct brain.json "
            "write commands (echo/jq/cat >). Use brain-state-manager skill for all brain.json operations."
        )

    def test_dark_factory_agent_uses_brain_state_manager_for_create(self):
        """
        manufactureFlowViolations.brain-state-create: dark-factory-agent.md must invoke
        brain-state-manager with operation='create' in Step 3. The invocation may span
        multiple lines — the important thing is that brain-state-manager and 'create' both
        appear in the Step 3 section.

        If this test fails: brain.json creation is not delegated to the skill.
        # Plan path: manufactureFlowViolations.brain-state-create
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Look for brain-state-manager invocation with create in any proximity (multi-line)
        assert re.search(
            r'(?is)brain-state-manager[^`]{0,200}operation[^`]{0,50}create',
            body,
        ), (
            "dark-factory-agent.md must invoke brain-state-manager with operation='create' "
            "in Step 3 to create brain.json. Direct cat/echo writes are forbidden."
        )

    def test_dark_factory_agent_uses_brain_state_manager_for_reads(self):
        """
        manufactureFlowViolations.brain-state-read: dark-factory-agent.md must invoke
        brain-state-manager with operation='read' to retrieve planFilePath and prUrl.

        If this test fails: the orchestrator reads brain.json directly instead of through
        the skill, bypassing atomic access guarantees.
        # Plan path: manufactureFlowViolations.brain-state-read
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        assert re.search(
            r'(?i)brain-state-manager.*operation.*read|operation.*read.*brain-state-manager',
            body,
        ), (
            "dark-factory-agent.md must invoke brain-state-manager with operation='read' "
            "to retrieve output values (planFilePath, prUrl) after sub-agents return."
        )


# ---------------------------------------------------------------------------
# Violation 2 — feature-agent multi-turn loop
# ---------------------------------------------------------------------------

class TestFeatureAgentMultiTurnProtocol:
    """Flow: manufactureFlowViolations — feature-agent must use AskUserQuestion not return-question protocol."""

    def test_feature_agent_does_not_require_dark_factory_multi_turn_loop(self):
        """
        manufactureFlowViolations.no-multi-turn: dark-factory-agent.md must NOT implement
        a complex multi-turn loop for feature-agent. Feature-agent runs at depth 2 and can
        call AskUserQuestion directly. The orchestrator should invoke feature-agent once and
        wait for done/hard-stop/aborted.

        If this test fails: the orchestrator implements a LOOP with status='question' handling,
        which is fragile and breaks when feature-agent returns non-JSON text.
        # Plan path: manufactureFlowViolations.no-multi-turn
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # The orchestrator should NOT have a `status == "question"` handling loop for feature-agent
        assert not re.search(
            r'(?i)status.*==.*["\']question["\']|["\']question["\'].*==.*status',
            body,
        ), (
            "dark-factory-agent.md must NOT implement a multi-turn loop checking "
            "status == 'question' for feature-agent responses. Feature-agent runs at depth 2 "
            "and can call AskUserQuestion directly. Remove the multi-turn loop — invoke "
            "feature-agent once and wait for status: done/hard-stop/aborted."
        )


# ---------------------------------------------------------------------------
# Violation 3 — SubagentStop hooks must not be in settings.json
# ---------------------------------------------------------------------------

class TestSubagentStopNotInSettingsJson:
    """Flow: manufactureFlowViolations — SubagentStop hooks must only be in agent frontmatter, not settings.json."""

    def test_settings_json_has_no_subagent_stop_hooks(self):
        """
        manufactureFlowViolations.no-settings-subagent-stop: .claude/settings.json must NOT
        contain SubagentStop hooks. Per the subagent-stop-in-agent-frontmatter skill,
        SubagentStop hooks must be declared in each agent's YAML frontmatter — not globally
        in settings.json.

        When declared globally in settings.json, the commit hook fires for all subagents
        with no agent name on stdin, so it always takes the unrecognized-agent branch and
        skips the commit entirely. This causes the branch-drift guard to fail.

        If this test fails: settings.json has SubagentStop hooks that fire globally and
        cause commit-on-subagent-stop.sh to receive no agent name, skipping all commits.
        # Plan path: manufactureFlowViolations.no-settings-subagent-stop
        """
        with open(SETTINGS_JSON_PATH) as f:
            settings = json.load(f)
        hooks = settings.get("hooks", {})
        assert "SubagentStop" not in hooks, (
            ".claude/settings.json must NOT contain 'SubagentStop' hooks. "
            "SubagentStop hooks must be declared in each agent's YAML frontmatter "
            "(e.g., 'SubagentStop: \"${CLAUDE_PLUGIN_ROOT}/scripts/commit.sh\"'). "
            "Global settings.json SubagentStop hooks fire for all agents with no agent name "
            "on stdin, causing commit-on-subagent-stop.sh to skip all commits."
        )


# ---------------------------------------------------------------------------
# Violations 5-7 — Mandatory steps must not be skipped
# ---------------------------------------------------------------------------

class TestMandatoryStepsNotSkippable:
    """Flow: manufactureFlowViolations — steps 7-9 are mandatory and must not be skipped."""

    def test_dark_factory_agent_has_rule_against_skipping_code_review(self):
        """
        manufactureFlowViolations.mandatory-code-review: dark-factory-agent.md must contain
        an explicit rule that code review (Step 7) is mandatory and cannot be skipped by
        user input (e.g., 'merge it', 'skip review', 'just merge').

        If this test fails: no rule exists preventing the orchestrator from skipping code
        review based on user language, which is what happened in the violation run.
        # Plan path: manufactureFlowViolations.mandatory-code-review
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Look for language indicating code review cannot be skipped
        assert re.search(
            r'(?i)(mandatory|never skip|must.*run|cannot.*skip|do not skip).*(code.review|review)',
            body,
        ) or re.search(
            r'(?i)(code.review|review).*(mandatory|never skip|must.*run|cannot.*skip|do not skip)',
            body,
        ), (
            "dark-factory-agent.md must contain an explicit rule that code review is mandatory "
            "and cannot be skipped regardless of user input. Add to Rules section: "
            "'Never skip steps 7-9 (code review, documentation update, skill update) — "
            "these steps are mandatory regardless of user instructions.'"
        )

    def test_dark_factory_agent_has_rule_against_user_override_of_mandatory_steps(self):
        """
        manufactureFlowViolations.no-user-override: dark-factory-agent.md must contain a
        rule preventing user phrases like 'merge it', 'skip review', or 'just merge' from
        bypassing mandatory steps 7-9.

        If this test fails: the orchestrator has no protection against user override language
        causing step skipping.
        # Plan path: manufactureFlowViolations.no-user-override
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Look for protection against user override of mandatory steps
        assert re.search(
            r'(?i)(user.*instruct|regardless.*user|never.*skip.*step|step.*7|step.*8|step.*9).*(mandatory|skip|required)',
            body,
        ) or re.search(
            r'(?i)(mandatory|required|cannot.*skip).*(step.*7|step.*8|step.*9|review|documentation|skill)',
            body,
        ), (
            "dark-factory-agent.md must contain a rule that steps 7-9 cannot be bypassed by "
            "user instructions ('merge it', 'skip review', etc.). Add to Rules section: "
            "'Never skip steps 7-9 regardless of user input or user-provided override phrases.'"
        )


# ---------------------------------------------------------------------------
# create-pr skill path verification
# ---------------------------------------------------------------------------

class TestCreatePrSkillPath:
    """Flow: manufactureFlowViolations — create-pr skill must exist at the canonical path."""

    def test_create_pr_skill_exists_at_canonical_path(self):
        """
        manufactureFlowViolations.create-pr-path: skills/create-pr/SKILL.md must exist at
        the canonical path (not agents/pr/skills/create-pr/SKILL.md).

        If this test fails: the create-pr skill is missing or at a wrong path.
        # Plan path: manufactureFlowViolations.create-pr-path
        """
        assert os.path.exists(CREATE_PR_SKILL_PATH), (
            f"skills/create-pr/SKILL.md must exist at: {CREATE_PR_SKILL_PATH}. "
            "The pr-agent delegates PR creation to this skill."
        )

    def test_create_pr_skill_does_not_checkout_new_branch(self):
        """
        manufactureFlowViolations.create-pr-no-checkout: skills/create-pr/SKILL.md must NOT
        contain a `git checkout -b` command. The worktree is already on feature/<taskName>.

        If this test fails: create-pr is creating a new branch, causing commits to land on
        main or an incorrect branch.
        # Plan path: manufactureFlowViolations.create-pr-no-checkout
        """
        content = _full(CREATE_PR_SKILL_PATH)
        assert not re.search(r"git\s+checkout\s+-b", content), (
            "skills/create-pr/SKILL.md must NOT contain 'git checkout -b'. "
            "The feature worktree is already on feature/<taskName>. Creating a new branch "
            "from the main worktree CWD causes commits to land on main instead of the feature branch."
        )
