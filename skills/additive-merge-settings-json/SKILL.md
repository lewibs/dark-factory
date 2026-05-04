---
name: additive-merge-settings-json
description: "When writing hooks or other structured data into .claude/settings.json, always read the existing file, merge new entries, and deduplicate — never overwrite the whole file."
user-invocable: false
---
## When to use

Any time a script or agent needs to add entries to `.claude/settings.json` — particularly the `hooks` key — without clobbering existing entries that were placed there by the user, another plugin, or a previous run.

## Steps

1. Read the existing file if it exists; treat a missing file as an empty object `{}`:
   ```python
   import json
   from pathlib import Path

   settings_path = Path(project_dir) / ".claude" / "settings.json"
   settings = {}
   if settings_path.exists():
       with open(settings_path, "r") as f:
           settings = json.load(f)
   ```

2. Navigate to the target key without replacing sibling keys:
   ```python
   if "hooks" not in settings:
       settings["hooks"] = {}
   existing = settings["hooks"]
   ```

3. Append new entries; deduplicate by the field that uniquely identifies an entry. For hook entries, deduplicate by exact command string across all matcher objects in the event list:
   ```python
   command_str = f"bash {hook_path}"
   already_present = any(
       entry.get("command") == command_str
       for matcher_obj in existing.get(event_type, [])
       for entry in matcher_obj.get("hooks", [])
   )
   if not already_present:
       existing.setdefault(event_type, []).append({
           "matcher": "",
           "hooks": [{"type": "command", "command": command_str}]
       })
   ```

4. Write the full settings dict back (not just the mutated sub-key):
   ```python
   settings["hooks"] = existing
   settings_path.parent.mkdir(parents=True, exist_ok=True)
   with open(settings_path, "w") as f:
       json.dump(settings, f, indent=2)
   ```

## Notes

- Always write the full `settings` dict back to disk, not just the sub-key you modified. Writing only `settings["hooks"]` to the file would delete all other top-level keys (e.g., `permissions`, `model`).
- `settings_path.parent.mkdir(parents=True, exist_ok=True)` handles the case where `.claude/` does not yet exist.
- Deduplication by command string is intentional: the same script path registered twice (e.g., from two `gen-hooks` runs) produces only one entry. If you need multiple different matchers for the same script, they will have different `matcher` values and will both be kept.
- For corrupted JSON, return an error rather than silently overwriting — a corrupt `settings.json` likely indicates a user error that should not be masked.
- The canonical implementation of this pattern lives in `scripts/gen_hooks.py` (`mergeIntoSettings` function).
