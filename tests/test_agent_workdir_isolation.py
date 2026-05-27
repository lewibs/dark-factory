"""
Regression tests for: update-documentation-agent and skill-update-agent write files
to main repo instead of isolated worktree.

Root causes verified:

1. update-documentation-agent: Phase 1 and Phase 3 use bare relative paths
   (tmp/update-docs-flows.md, docs/docs/<flow>.md) without any WORK_DIR prefix.
   The agent also never receives WORK_DIR from dark-factory-agent's batch invocation.

2. skill-update-agent: Step 4 constructs skillPath = "skills/<slug>/SKILL.md" as a
   relative string. The write uses that relative path without joining it to workDir,
   so the file lands in CWD (main repo root) instead of workDir.

3. dark-factory-agent: Step 8 batch invocation of update-documentation-agent passes
   only {planFilePath} — WORK_DIR is not included in the agent args.

Fix contract (each test defines what the fixed state must look like):
- update-documentation-agent must resolve WORK_DIR before Phase 1 writes.
- All doc file writes must use $WORK_DIR-prefixed paths.
- dark-factory-agent must pass workDir to update-documentation-agent batch invocation.
- skill-update-agent must join skillPath to workDir before every write/read operation.

See: docs/bugs/2026-05-06-agents-write-docs-to-main-repo-not-worktree.md
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPDATE_DOC_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "documentation", "agents", "update-documentation-agent.md"
)
SKILL_UPDATE_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "skill-update", "agents", "skill-update-agent.md"
)
DARK_FACTORY_AGENT_PATH = os.path.join(
    PROJECT_ROOT, "agents", "dark-factory", "agents", "dark-factory-agent.md"
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
# update-documentation-agent: WORK_DIR resolution must exist before file writes
# ---------------------------------------------------------------------------

class TestUpdateDocumentationAgentWorkDir:
    """Flow: agentWorkdirIsolation — update-documentation-agent must resolve WORK_DIR before writing."""

    def test_resolves_work_dir_before_phases(self):
        """
        agentWorkdirIsolation.update-doc-resolves-workdir: update-documentation-agent must
        contain a WORK_DIR resolution block that appears before Phase 1 (before any file write).
        The resolution block must read DARK_FACTORY_WORK_DIR env var and fall back to
        /tmp/dark-factory-work-dir pointer file.
        """
        content = _full(UPDATE_DOC_AGENT_PATH)
        # Find WORK_DIR resolution
        workdir_resolution_pattern = re.compile(
            r"WORK_DIR\s*=\s*\$DARK_FACTORY_WORK_DIR", re.MULTILINE
        )
        match = workdir_resolution_pattern.search(content)
        assert match is not None, (
            "update-documentation-agent must resolve WORK_DIR via $DARK_FACTORY_WORK_DIR "
            "before any file write. No WORK_DIR resolution found."
        )

        # Resolution must appear before "Phase 1"
        phase1_pos = content.find("Phase 1")
        assert phase1_pos != -1, "update-documentation-agent must have a 'Phase 1' section"
        assert match.start() < phase1_pos, (
            "WORK_DIR resolution must appear BEFORE Phase 1. "
            f"Resolution at char {match.start()}, Phase 1 at char {phase1_pos}."
        )

    def test_tmp_checklist_uses_work_dir_prefix(self):
        """
        agentWorkdirIsolation.update-doc-tmp-path: update-documentation-agent Phase 1 must write
        the flows checklist to $WORK_DIR/tmp/update-docs-flows.md, not bare tmp/update-docs-flows.md.
        """
        content = _full(UPDATE_DOC_AGENT_PATH)
        # Bare path must not appear as a file write target
        bare_path_pattern = re.compile(r"(?<!WORK_DIR/)(?<!\$WORK_DIR/)tmp/update-docs-flows\.md")
        # We only flag occurrences that are NOT preceded by WORK_DIR prefix
        # More precisely: any occurrence of `tmp/update-docs-flows.md` without $WORK_DIR/
        lines_with_bare = [
            line.strip()
            for line in content.splitlines()
            if "tmp/update-docs-flows.md" in line
            and "$WORK_DIR/tmp/update-docs-flows.md" not in line
        ]
        assert lines_with_bare == [], (
            "update-documentation-agent must use $WORK_DIR/tmp/update-docs-flows.md, "
            f"not bare path. Found bare references: {lines_with_bare}"
        )

    def test_docs_writes_use_work_dir_prefix(self):
        """
        agentWorkdirIsolation.update-doc-docs-path: update-documentation-agent Phase 3 must write
        doc files to $WORK_DIR/docs/docs/<flow>.md, not bare docs/docs/<flow>.md.
        """
        content = _full(UPDATE_DOC_AGENT_PATH)
        # Any line that creates/writes a docs/docs/ path must include $WORK_DIR prefix
        lines_with_bare_docs = [
            line.strip()
            for line in content.splitlines()
            if re.search(r"(?<!\$WORK_DIR/)docs/docs/", line)
            and "docs/docs/" in line
        ]
        assert lines_with_bare_docs == [], (
            "update-documentation-agent must use $WORK_DIR/docs/docs/ for all doc file "
            f"writes. Found bare references: {lines_with_bare_docs}"
        )


# ---------------------------------------------------------------------------
# dark-factory-agent: must pass workDir to update-documentation-agent batch invocation
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not os.path.exists(DARK_FACTORY_AGENT_PATH), reason="dark-factory-agent.md removed (deprecated agent)")
class TestDarkFactoryAgentPassesWorkDir:
    """Flow: agentWorkdirIsolation — dark-factory-agent must pass workDir to update-documentation-agent.

    NOTE: dark-factory-agent was removed as it is deprecated and not referenced by any active command.
    This test is skipped.
    """

    def test_update_doc_batch_invocation_includes_work_dir(self):
        """
        agentWorkdirIsolation.dark-factory-passes-workdir: dark-factory-agent Step 8 must pass
        workDir (or WORK_DIR) as an argument when invoking update-documentation-agent via
        queue_batch_job. Currently it only passes {planFilePath}.
        """
        content = _full(DARK_FACTORY_AGENT_PATH)
        # Find all queue_batch_job calls for update-documentation-agent
        batch_call_pattern = re.compile(
            r'queue_batch_job\("update-documentation-agent",\s*\{([^}]+)\}',
            re.MULTILINE | re.DOTALL,
        )
        matches = batch_call_pattern.findall(content)
        assert len(matches) > 0, (
            "dark-factory-agent must have at least one queue_batch_job call for "
            "update-documentation-agent"
        )
        for args_str in matches:
            assert re.search(r"\bwork[Dd]ir\b|\bWORK_DIR\b", args_str), (
                "dark-factory-agent queue_batch_job for update-documentation-agent must "
                f"include workDir/WORK_DIR in args. Found args: {{{args_str.strip()}}}"
            )


# ---------------------------------------------------------------------------
# skill-update-agent: skillPath must be joined to workDir before any file operation
# ---------------------------------------------------------------------------

class TestSkillUpdateAgentWorkDir:
    """Flow: agentWorkdirIsolation — skill-update-agent must join skillPath to workDir."""

    def test_skill_path_joined_to_work_dir(self):
        """
        agentWorkdirIsolation.skill-update-workdir-join: skill-update-agent Step 4 must construct
        skillPath by joining workDir with "skills/<slug>/SKILL.md", not as a bare relative string.
        The instruction text must demonstrate the join so that LLM execution uses the absolute path.
        """
        content = _full(SKILL_UPDATE_AGENT_PATH)
        # The skill path construction must reference workDir
        # Accept any of: workDir + "/skills/...", workDir/skills/, $WORK_DIR/skills/, os.path.join(workDir, ...)
        skill_path_pattern = re.compile(
            r"(workDir\s*[\+/]\s*[\"']?/?skills/"
            r"|os\.path\.join\(workDir"
            r"|\$WORK_DIR/skills/"
            r"|workDir \+ .?/skills/)",
            re.MULTILINE,
        )
        match = skill_path_pattern.search(content)
        assert match is not None, (
            "skill-update-agent Step 4 must construct skillPath by joining workDir with "
            "'skills/<slug>/SKILL.md'. Bare relative path 'skills/<slug>/SKILL.md' without "
            "workDir join causes writes to land in CWD (main repo root). "
            "No workDir-joined skill path construction found."
        )

    def test_no_bare_skill_path_assignment(self):
        """
        agentWorkdirIsolation.skill-update-no-bare-path: skill-update-agent must not assign
        skillPath as a bare 'skills/<slug>/SKILL.md' without workDir prefix.
        """
        content = _full(SKILL_UPDATE_AGENT_PATH)
        # Lines that set skillPath to a bare relative path (no workDir join on same line)
        bare_assignments = [
            line.strip()
            for line in content.splitlines()
            if re.search(r'skillPath\s*=\s*["\']?skills/', line)
            and not re.search(r'workDir|WORK_DIR', line)
        ]
        assert bare_assignments == [], (
            "skill-update-agent must not assign skillPath as a bare relative path without "
            f"workDir. Found bare assignments: {bare_assignments}"
        )
