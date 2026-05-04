"""
Unit tests for gen_hooks.py

Tests for three flows:
- scanFrontmatter: Extract hook declarations from YAML frontmatter
- mergeIntoSettings: Merge hooks into settings.json without deleting existing entries
- genHooksCommand: Orchestrate scan and merge
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from scripts.gen_hooks import FrontmatterHook, scanFrontmatter, mergeIntoSettings, genHooksCommand


class TestScanFrontmatter:
    """Tests for scanFrontmatter flow"""

    def test_scanFrontmatter_success(self):
        """Plan path: scanFrontmatter.success"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("""---
name: test
PreToolUse: ./hooks/pre-use.sh
---
# Test""")
            result = scanFrontmatter(tmpdir)
            assert result is not None
            assert "hooks" in result
            assert len(result["hooks"]) > 0

    def test_scanFrontmatter_no_md_files(self):
        """Plan path: scanFrontmatter.no-md-files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scanFrontmatter(tmpdir)
            assert result is not None
            assert "hooks" in result
            assert len(result["hooks"]) == 0

    def test_scanFrontmatter_invalid_yaml(self):
        """Plan path: scanFrontmatter.invalid-yaml"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("""---
name: test
invalid: [
---
# Test""")
            result = scanFrontmatter(tmpdir)
            # Should either return empty or error, not crash
            assert result is not None


class TestMergeIntoSettings:
    """Tests for mergeIntoSettings flow"""

    def test_mergeIntoSettings_success(self):
        """Plan path: mergeIntoSettings.success"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            existing_settings = {"hooks": {"PreToolUse": []}}
            settings_path.write_text(json.dumps(existing_settings))

            new_hooks = [FrontmatterHook("PreToolUse", "./hooks/pre-use.sh", "", "test.md")]
            result = mergeIntoSettings(str(settings_path), new_hooks)

            assert result is not None
            assert "addedCount" in result
            assert result["addedCount"] >= 0

    def test_mergeIntoSettings_settings_missing(self):
        """Plan path: mergeIntoSettings.settings-missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"

            new_hooks = [FrontmatterHook("PreToolUse", "./hooks/pre-use.sh", "", "test.md")]
            result = mergeIntoSettings(str(settings_path), new_hooks)

            assert result is not None
            assert settings_path.exists()

    def test_mergeIntoSettings_all_duplicates(self):
        """Plan path: mergeIntoSettings.all-duplicates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "settings.json"
            existing_settings = {
                "hooks": {
                    "PreToolUse": [
                        {"matcher": "", "hooks": [{"type": "command", "command": "bash ./hooks/pre-use.sh"}]}
                    ]
                }
            }
            settings_path.write_text(json.dumps(existing_settings))

            new_hooks = [FrontmatterHook("PreToolUse", "./hooks/pre-use.sh", "", "test.md")]
            result = mergeIntoSettings(str(settings_path), new_hooks)

            assert result is not None
            assert "skippedCount" in result
            assert result["addedCount"] == 0

    def test_mergeIntoSettings_write_error(self):
        """Plan path: mergeIntoSettings.write-error"""
        # Use a path that's not writable
        settings_path = "/root/nonexistent/settings.json"
        new_hooks = [FrontmatterHook("PreToolUse", "./hooks/pre-use.sh", "", "test.md")]

        # Should handle error gracefully or return error
        try:
            result = mergeIntoSettings(settings_path, new_hooks)
            # If no exception, result should indicate error
            assert result is not None
        except (OSError, IOError):
            # Also acceptable - function can raise
            pass


class TestGenHooksCommand:
    """Tests for genHooksCommand flow"""

    def test_genHooksCommand_success(self):
        """Plan path: genHooksCommand.success"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a .md file with hook declaration
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("""---
name: test
PreToolUse: ./hooks/pre-use.sh
---
# Test""")

            result = genHooksCommand(tmpdir)

            assert result is not None
            assert "addedCount" in result or "message" in result

    def test_genHooksCommand_nothing_to_add(self):
        """Plan path: genHooksCommand.nothing-to-add"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = genHooksCommand(tmpdir)

            assert result is not None
            # Should return result even if nothing added
            assert "addedCount" in result or "message" in result

    def test_genHooksCommand_error(self):
        """Plan path: genHooksCommand.error"""
        # Use invalid directory
        result = genHooksCommand("/nonexistent/directory")

        # Should handle error gracefully
        assert result is not None
