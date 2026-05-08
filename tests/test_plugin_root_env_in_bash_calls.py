"""
Regression test for: manufacture halts after task-classifier because CLAUDE_PLUGIN_ROOT
is empty in Bash tool call subprocesses.

Root cause: dark-factory-agent.md's orchestration pseudocode used ${CLAUDE_PLUGIN_ROOT}
directly in Bash tool call commands (e.g. bash "${CLAUDE_PLUGIN_ROOT}/agents/...").
${CLAUDE_PLUGIN_ROOT} is injected by the plugin runtime for hook scripts only — not for
the LLM's Bash tool call subprocesses. When the variable is empty, the path becomes
"/agents/dark-factory/scripts/prep-feature-dir.sh" which does not exist, causing the
bash call to fail. Per the agent's instructions, script failure causes it to STOP,
which manifests as the orchestration halting silently after task-classifier returns.

Fix: Resolve the plugin root at runtime from installed_plugins.json instead of relying
on ${CLAUDE_PLUGIN_ROOT} being present in the Bash subprocess environment.

See: docs/bugs/2026-05-07-manufacture-stuck-after-task-classifier.md

Flow: pluginRootEnvInBashCalls
"""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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


def _frontmatter(path: str) -> str:
    """Return just the YAML frontmatter of an agent/skill file."""
    with open(path) as f:
        content = f.read()
    # frontmatter is between the first --- and the second ---
    if not content.startswith("---"):
        return ""
    end = content.find("\n---", 4)
    return content[:end] if end != -1 else ""


class TestPluginRootNotUsedInBashCalls:
    """
    Flow: pluginRootEnvInBashCalls — dark-factory-agent.md must not reference
    ${CLAUDE_PLUGIN_ROOT} inside Bash tool call pseudocode, because that variable
    is empty in the bash subprocess environment (it is only set for hook scripts).
    """

    def test_dark_factory_agent_body_does_not_use_claude_plugin_root_in_bash_calls(self):
        """
        pluginRootEnvInBashCalls.no-claude-plugin-root-in-bash: The orchestration pseudocode
        in dark-factory-agent.md must NOT contain bash("${CLAUDE_PLUGIN_ROOT}/...") calls.
        ${CLAUDE_PLUGIN_ROOT} is only available in Claude Code hook command environments
        (PreToolUse, PostToolUse, Stop, SubagentStop), NOT in Bash tool call subprocesses.
        When used in Bash tool calls, the variable expands to an empty string, producing
        invalid paths like "/agents/dark-factory/scripts/prep-feature-dir.sh" that do not
        exist, causing the orchestrator to halt.

        The fix is to resolve the plugin root from installed_plugins.json at runtime
        using a python3 -c invocation.

        If this test fails: dark-factory-agent.md contains ${CLAUDE_PLUGIN_ROOT} in a bash()
        pseudocode call, which will silently produce an empty path and cause the orchestrator
        to stop after task-classifier returns.
        # Plan path: pluginRootEnvInBashCalls.no-claude-plugin-root-in-bash
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Extract only the orchestration pseudocode block (between the first ``` and matching ```)
        code_block = re.search(r"```\n(.*?)\n```", body, re.DOTALL)
        code = code_block.group(1) if code_block else body

        # Detect bash("${CLAUDE_PLUGIN_ROOT}/...") or bash("$CLAUDE_PLUGIN_ROOT/...")
        # patterns inside bash() pseudocode calls
        matches = re.findall(
            r'bash\s*\(["\']?\s*["\']?\$\{?CLAUDE_PLUGIN_ROOT\}?/',
            code,
            re.IGNORECASE,
        )
        assert not matches, (
            f"dark-factory-agent.md orchestration pseudocode contains "
            f"{len(matches)} bash() call(s) referencing ${{CLAUDE_PLUGIN_ROOT}}: {matches}. "
            "CLAUDE_PLUGIN_ROOT is empty in Bash tool call subprocesses. "
            "Resolve the plugin root from installed_plugins.json instead:\n"
            "  PLUGIN_ROOT = bash(\"python3 -c \\\"import json,os; "
            "d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json'))); "
            "p=d['plugins'].get('dark-factory@dark-factory',[]); "
            "print(p[0].get('installPath','') if p else '')\\\"\")\n"
            "Then use $PLUGIN_ROOT instead of ${CLAUDE_PLUGIN_ROOT} in script paths."
        )

    def test_dark_factory_agent_resolves_plugin_root_from_installed_plugins(self):
        """
        pluginRootEnvInBashCalls.resolves-from-installed-plugins: dark-factory-agent.md
        must contain a python3-based resolution of the plugin root from installed_plugins.json
        before calling any plugin scripts (prep-feature-dir.sh, cleanup-worktree.sh, etc.).

        If this test fails: the agent has no mechanism to discover the plugin install path,
        meaning it must rely on ${CLAUDE_PLUGIN_ROOT} which is not available in Bash subprocesses.
        # Plan path: pluginRootEnvInBashCalls.resolves-from-installed-plugins
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        # Look for the installed_plugins.json resolution pattern
        assert re.search(
            r'installed_plugins\.json',
            body,
        ), (
            "dark-factory-agent.md must resolve the plugin root from "
            "~/.claude/plugins/installed_plugins.json (not from ${CLAUDE_PLUGIN_ROOT}) "
            "because CLAUDE_PLUGIN_ROOT is not available in Bash tool call subprocesses. "
            "Add: PLUGIN_ROOT = bash(\"python3 -c \\\"import json,os; "
            "d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json'))); "
            "p=d['plugins'].get('dark-factory@dark-factory',[]); "
            "print(p[0].get('installPath','') if p else '')\\\"\")"
        )

    def test_dark_factory_agent_allowed_tools_uses_glob_not_claude_plugin_root(self):
        """
        pluginRootEnvInBashCalls.allowed-tools-glob: The allowed-tools frontmatter in
        dark-factory-agent.md must use glob patterns (e.g., */agents/dark-factory/scripts/*)
        rather than ${CLAUDE_PLUGIN_ROOT}/... patterns, because the CLAUDE_PLUGIN_ROOT
        variable may not expand correctly in allowed-tools at agent load time.

        If this test fails: the allowed-tools still reference ${CLAUDE_PLUGIN_ROOT},
        which may not match the resolved path used in actual bash calls.
        # Plan path: pluginRootEnvInBashCalls.allowed-tools-glob
        """
        fm = _frontmatter(DARK_FACTORY_AGENT_PATH)
        # Extract the allowed-tools line
        allowed_tools_match = re.search(r'^allowed-tools:\s*(.+)$', fm, re.MULTILINE)
        if not allowed_tools_match:
            return  # No allowed-tools — nothing to check

        allowed_tools_line = allowed_tools_match.group(1)
        # Check that CLAUDE_PLUGIN_ROOT does not appear in allowed-tools patterns
        # for script paths (it's fine if it appears in comments)
        assert "${CLAUDE_PLUGIN_ROOT}" not in allowed_tools_line, (
            "dark-factory-agent.md allowed-tools frontmatter must NOT use ${CLAUDE_PLUGIN_ROOT}. "
            "Use glob patterns like */agents/dark-factory/scripts/prep-feature-dir.sh * instead. "
            "CLAUDE_PLUGIN_ROOT may not expand correctly when allowed-tools is processed at "
            "agent load time, causing permission mismatches with the resolved runtime paths."
        )

    def test_dark_factory_agent_has_forbidden_rule_about_claude_plugin_root(self):
        """
        pluginRootEnvInBashCalls.forbidden-rule: dark-factory-agent.md must contain an
        explicit FORBIDDEN rule warning against using ${CLAUDE_PLUGIN_ROOT} inside Bash
        tool call pseudocode.

        If this test fails: there is no documentation warning future editors about this
        footgun, increasing the risk of regression.
        # Plan path: pluginRootEnvInBashCalls.forbidden-rule
        """
        body = _body(DARK_FACTORY_AGENT_PATH)
        assert re.search(
            r'(?i)FORBIDDEN.*CLAUDE_PLUGIN_ROOT|CLAUDE_PLUGIN_ROOT.*FORBIDDEN',
            body,
        ), (
            "dark-factory-agent.md must contain an explicit FORBIDDEN rule about "
            "${CLAUDE_PLUGIN_ROOT} in Bash tool call pseudocode. "
            "Add to Rules section: "
            "'FORBIDDEN: Never use ${CLAUDE_PLUGIN_ROOT} inside Bash tool call pseudocode "
            "— it is empty in Bash tool call subprocesses. Always resolve plugin root via "
            "installed_plugins.json before calling plugin scripts.'"
        )

    def test_plugin_root_resolution_command_is_syntactically_valid(self):
        """
        pluginRootEnvInBashCalls.resolution-syntax: The python3 command used to resolve
        PLUGIN_ROOT from installed_plugins.json must produce the correct path when executed
        (i.e., it must be syntactically valid and find the dark-factory plugin via explicit
        name lookup).

        If this test fails: the resolution command in dark-factory-agent.md is malformed
        or points to a non-existent file, meaning the agent would fail at runtime even
        with the fix applied.
        # Plan path: pluginRootEnvInBashCalls.resolution-syntax
        """
        import json
        import subprocess

        # Run the resolution command as the LLM would
        # Uses explicit plugin name lookup to handle multiple installed plugins
        cmd = (
            "python3 -c \""
            "import json,os; "
            "d=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json'))); "
            "p=d['plugins'].get('dark-factory@dark-factory',[]); "
            "print(p[0].get('installPath','') if p else '')"
            "\""
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Plugin root resolution command failed with exit code {result.returncode}. "
            f"stderr: {result.stderr.strip()}"
        )
        plugin_root = result.stdout.strip()
        assert plugin_root, "Plugin root resolution command returned empty output."

        # Verify the resolved path contains the expected scripts
        prep_script = os.path.join(
            plugin_root, "agents", "dark-factory", "scripts", "prep-feature-dir.sh"
        )
        assert os.path.exists(prep_script), (
            f"prep-feature-dir.sh not found at resolved plugin root: {prep_script}. "
            f"Resolved PLUGIN_ROOT was: {plugin_root}"
        )

        cleanup_script = os.path.join(
            plugin_root, "agents", "dark-factory", "scripts", "cleanup-worktree.sh"
        )
        assert os.path.exists(cleanup_script), (
            f"cleanup-worktree.sh not found at resolved plugin root: {cleanup_script}. "
            f"Resolved PLUGIN_ROOT was: {plugin_root}"
        )
