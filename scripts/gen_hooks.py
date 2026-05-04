#!/usr/bin/env python3
"""
gen_hooks.py - Scans YAML frontmatter for hook declarations and merges into .claude/settings.json

Flows:
- scanFrontmatter: Recursively scan .md files for hook declarations in YAML frontmatter
- mergeIntoSettings: Merge discovered hooks into .claude/settings.json without deleting existing entries
- genHooksCommand: Orchestrates scan + merge and returns summary to user
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class FrontmatterHook:
    """Represents a single hook declaration extracted from YAML frontmatter"""
    def __init__(self, eventType: str, command: str, matcher: str, sourceFile: str):
        self.eventType = eventType
        self.command = command
        self.matcher = matcher
        self.sourceFile = sourceFile


# Hook event types supported by Claude Code
HOOK_TYPES = {"PreToolUse", "PostToolUse", "Stop", "SubagentStop", "PreCompact"}


def _parse_yaml_frontmatter(file_path: str) -> Optional[Dict[str, Any]]:
    """Extract YAML frontmatter from a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file starts with ---
        if not content.startswith('---'):
            return None

        # Find the closing ---
        lines = content.split('\n')
        closing_index = None
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                closing_index = i
                break

        if closing_index is None:
            return None

        # Extract frontmatter
        frontmatter_str = '\n'.join(lines[1:closing_index])
        frontmatter = yaml.safe_load(frontmatter_str)

        return frontmatter if isinstance(frontmatter, dict) else None
    except Exception:
        # Return None for unparseable files
        return None


def _ensure_list(value: Any) -> List[Any]:
    """Convert single value to list, or return list as-is."""
    if isinstance(value, list):
        return value
    return [value] if value is not None else []


def scanFrontmatter(rootDir: str) -> Dict[str, Any]:
    """
    Flow: scanFrontmatter
    Parse YAML frontmatter from all .md files and extract hook declarations
    """
    results = []

    try:
        root_path = Path(rootDir)
        if not root_path.exists():
            return {"hooks": []}

        # Recursively scan all .md files
        for md_file in root_path.rglob('*.md'):
            frontmatter = _parse_yaml_frontmatter(str(md_file))
            if frontmatter is None:
                continue

            # Look for hook declarations in frontmatter
            for key in frontmatter:
                if key in HOOK_TYPES:
                    values = _ensure_list(frontmatter[key])
                    for value in values:
                        hook = FrontmatterHook(
                            eventType=key,
                            command=value,
                            matcher="",
                            sourceFile=str(md_file)
                        )
                        results.append(hook)
    except Exception:
        pass

    return {"hooks": results}


def mergeIntoSettings(settingsPath: str, newHooks: List[FrontmatterHook]) -> Dict[str, Any]:
    """
    Flow: mergeIntoSettings
    Merge new hooks into existing settings.json without deleting existing entries
    """
    try:
        # Read existing settings or create empty dict
        settings = {}
        settings_path = Path(settingsPath)
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception:
                settings = {}

        # Get or create hooks key
        if "hooks" not in settings:
            settings["hooks"] = {}

        existing = settings["hooks"]
        added = 0
        skipped = 0

        for hook in newHooks:
            # Create event list if needed
            if hook.eventType not in existing:
                existing[hook.eventType] = []

            event_list = existing[hook.eventType]

            # Build command string
            command_str = f"bash {hook.command}"

            # Check for duplicate
            already_present = False
            for matcher_obj in event_list:
                for entry in matcher_obj.get("hooks", []):
                    if entry.get("command") == command_str:
                        already_present = True
                        break
                if already_present:
                    break

            if already_present:
                skipped += 1
            else:
                # Add new hook entry
                event_list.append({
                    "matcher": hook.matcher,
                    "hooks": [{"type": "command", "command": command_str}]
                })
                added += 1

        # Write updated settings
        settings["hooks"] = existing
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)

        return {
            "addedCount": added,
            "skippedCount": skipped,
            "settingsPath": settingsPath
        }
    except Exception as e:
        return {
            "message": f"Error writing settings: {str(e)}"
        }


def genHooksCommand(projectDir: str) -> Dict[str, Any]:
    """
    Flow: genHooksCommand
    Orchestrate scanFrontmatter + mergeIntoSettings and return summary
    """
    try:
        # Step 1: Scan for frontmatter hooks
        scan_result = scanFrontmatter(projectDir)
        if "message" in scan_result:
            return scan_result

        hooks = scan_result.get("hooks", [])

        # Step 2: Merge into settings.json
        settings_path = os.path.join(projectDir, ".claude", "settings.json")
        merge_result = mergeIntoSettings(settings_path, hooks)

        if "message" in merge_result:
            return merge_result

        added_count = merge_result.get("addedCount", 0)
        skipped_count = merge_result.get("skippedCount", 0)

        message = f"Added {added_count} hook(s), skipped {skipped_count} duplicate(s)."

        return {
            "addedCount": added_count,
            "skippedCount": skipped_count,
            "settingsPath": settings_path,
            "message": message
        }
    except Exception as e:
        return {
            "message": f"Error: {str(e)}"
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        projectDir = sys.argv[1]
    else:
        projectDir = os.getcwd()
    result = genHooksCommand(projectDir)
    print(result)
