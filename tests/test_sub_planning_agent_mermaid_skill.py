"""
Regression test: sub-planning-agent must correctly reference the create-mermaid-diagram skill
so that generated plan diagrams follow the required formatting standards.

Three bugs prevented the skill from being applied:

1. Wrong frontmatter format: skills: used a path (skills/create-mermaid-diagram/SKILL.md)
   instead of the slug (create-mermaid-diagram). The plugin loader expects slugs in frontmatter.

2. Passive skill reference in mermaid phase: "follow the skill" does not give the LLM an
   explicit invocation instruction. Must say "invoke the skill at <path>".

3. draft_plan phase skips skill entirely: the phase creates a mermaid placeholder without any
   instruction to invoke the create-mermaid-diagram skill for proper formatting.

See: docs/bugs/2026-05-27-planning-flow-mermaid-skill-not-invoked.md

Flow: subPlanningAgentMermaidSkill
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUB_PLANNING_AGENT_PATH = os.path.join(
    PROJECT_ROOT,
    "agents",
    "featurework",
    "planning",
    "agents",
    "sub-planning-agent.md",
)

SKILL_PATH = "skills/create-mermaid-diagram/SKILL.md"
SKILL_SLUG = "create-mermaid-diagram"


def _frontmatter(path: str) -> str:
    """Return the YAML front-matter string (between the two --- delimiters)."""
    with open(path) as f:
        content = f.read()
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    return fm_match.group(1) if fm_match else ""


def _body(path: str) -> str:
    """Return the body of an agent file (everything after the closing front-matter ---)."""
    with open(path) as f:
        content = f.read()
    fm_end = content.find("\n---", 4)
    return content[fm_end + 4:] if fm_end != -1 else content


class TestSubPlanningAgentMermaidSkill:
    """Flow: subPlanningAgentMermaidSkill — create-mermaid-diagram skill must be correctly referenced"""

    def test_skills_frontmatter_uses_slug_not_path(self):
        """
        subPlanningAgentMermaidSkill.frontmatter-slug: the skills: frontmatter field must list
        the skill as a slug (create-mermaid-diagram), not as a path
        (skills/create-mermaid-diagram/SKILL.md).

        The plugin loader expects slugs in the skills: frontmatter field. A path form is for
        prose instructions in agent bodies, not for frontmatter metadata declarations.
        (See: skills/reference-skills-by-path/SKILL.md)

        If this test fails: the skills: frontmatter has been reverted to path form.
        # Plan path: subPlanningAgentMermaidSkill.frontmatter-slug
        """
        fm = _frontmatter(SUB_PLANNING_AGENT_PATH)
        assert fm, "sub-planning-agent.md must have YAML front-matter"

        # Must contain the slug form
        assert SKILL_SLUG in fm, (
            f"sub-planning-agent.md skills: frontmatter must list '{SKILL_SLUG}' (slug form). "
            f"Found frontmatter:\n{fm}"
        )

        # Must NOT contain the path form in frontmatter
        assert "skills/create-mermaid-diagram/SKILL.md" not in fm, (
            "sub-planning-agent.md skills: frontmatter must NOT use the path form "
            "'skills/create-mermaid-diagram/SKILL.md'. Use the slug 'create-mermaid-diagram' instead. "
            "Path references belong in prose instructions, not frontmatter metadata."
        )

    def test_mermaid_phase_uses_invoke_not_follow(self):
        """
        subPlanningAgentMermaidSkill.mermaid-invoke: the mermaid phase instruction must use
        "invoke the skill at skills/create-mermaid-diagram/SKILL.md", not "follow the ... skill".

        The word "follow" is passive and does not give the LLM a clear instruction to invoke
        the skill via the Skill tool. "invoke the skill at <path>" is the required form per
        skills/reference-skills-by-path/SKILL.md.

        If this test fails: the mermaid phase instruction was reverted to a passive reference.
        # Plan path: subPlanningAgentMermaidSkill.mermaid-invoke
        """
        body = _body(SUB_PLANNING_AGENT_PATH)

        # Must use "invoke" with the explicit skill path in the mermaid phase
        assert re.search(r"invoke the skill at `?skills/create-mermaid-diagram/SKILL\.md`?", body), (
            "sub-planning-agent.md mermaid phase must say "
            "'invoke the skill at `skills/create-mermaid-diagram/SKILL.md`' "
            "to explicitly direct the LLM to load and apply the skill. "
            "A passive 'follow the skill' instruction is insufficient."
        )

        # Must NOT use the passive "follow" form for the mermaid skill
        assert not re.search(r"follow the `?create-mermaid-diagram`? skill", body), (
            "sub-planning-agent.md must not use the passive 'follow the create-mermaid-diagram skill' "
            "instruction. Replace it with 'invoke the skill at `skills/create-mermaid-diagram/SKILL.md`'."
        )

    def test_draft_plan_phase_instructs_skill_invocation(self):
        """
        subPlanningAgentMermaidSkill.draft-plan-invoke: the draft_plan phase must include an
        instruction to invoke the create-mermaid-diagram skill when creating the placeholder
        mermaid diagram section.

        Without this instruction the draft_plan phase copies the bare template placeholder
        (generic graph TD A --> B) without applying color classes, labeled edges, or the other
        formatting rules from the skill.

        If this test fails: the draft_plan phase no longer instructs skill invocation for the
        mermaid section.
        # Plan path: subPlanningAgentMermaidSkill.draft-plan-invoke
        """
        body = _body(SUB_PLANNING_AGENT_PATH)

        # Locate the draft_plan phase section
        draft_plan_match = re.search(
            r"## Phase: draft_plan(.*?)(?=## Phase:|\Z)", body, re.DOTALL
        )
        assert draft_plan_match, (
            "sub-planning-agent.md must contain a '## Phase: draft_plan' section."
        )
        draft_plan_section = draft_plan_match.group(1)

        # The draft_plan section must mention invoking the mermaid skill
        assert re.search(r"invoke.*skill.*create-mermaid|create-mermaid.*skill.*invoke", draft_plan_section, re.IGNORECASE), (
            "sub-planning-agent.md ## Phase: draft_plan section must instruct the agent to invoke "
            "the skill at `skills/create-mermaid-diagram/SKILL.md` when creating the mermaid diagram "
            "placeholder. Without this, the draft diagram is a bare template copy with no formatting."
        )
