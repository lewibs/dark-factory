#!/usr/bin/env python3
"""
gen_hooks.py - Scan agent/skill/command files for hook declarations and sync to hooks/hooks.json

Scans all .md files under agents/, skills/, and commands/ directories for hook declarations
in YAML frontmatter, then merges them into hooks/hooks.json without duplicates.

Hook declaration format in frontmatter:
  hooks:
    - event: PreToolUse
      matcher: "Agent"
      script: agents/featurework/scripts/my-hook.sh
"""

import os
import json
import sys
import glob
from pathlib import Path


def get_plugin_root():
    """Get the CLAUDE_PLUGIN_ROOT environment variable or exit with error."""
    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT')
    if not plugin_root:
        print("Error: CLAUDE_PLUGIN_ROOT environment variable is not set", file=sys.stderr)
        sys.exit(1)
    return plugin_root


def parse_frontmatter(file_path):
    """Parse YAML frontmatter from a markdown file.
    
    Returns a dict with frontmatter key-value pairs, or empty dict if no frontmatter.
    Handles malformed YAML gracefully.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file starts with ---
        if not content.startswith('---'):
            return {}
        
        # Find the closing --- (second occurrence)
        lines = content.split('\n')
        if len(lines) < 2:
            return {}
        
        # Find the second --- delimiter
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_idx = i
                break
        
        if end_idx is None:
            return {}
        
        # Extract frontmatter content
        frontmatter_text = '\n'.join(lines[1:end_idx])
        
        # Parse YAML manually (simple key: value pairs)
        frontmatter = {}
        in_hooks = False
        hooks_list = []
        current_hook = {}
        
        for line in frontmatter_text.split('\n'):
            line = line.rstrip()
            
            # Check for hooks: section start
            if line.strip().startswith('hooks:'):
                in_hooks = True
                continue
            
            if in_hooks:
                # Check for list item (- event: ...)
                if line.strip().startswith('- '):
                    # If we have a previous hook, save it
                    if current_hook:
                        hooks_list.append(current_hook)
                    current_hook = {}
                    # Parse the first field on this line
                    rest = line.strip()[2:].strip()
                    if ':' in rest:
                        key, val = rest.split(':', 1)
                        current_hook[key.strip()] = val.strip().strip('"\'')
                elif line.strip().startswith('event:') or line.strip().startswith('matcher:') or line.strip().startswith('script:'):
                    # Parse key: value pair within a hook
                    key, val = line.strip().split(':', 1)
                    current_hook[key.strip()] = val.strip().strip('"\'')
                elif line and not line[0].isspace() and ':' in line:
                    # We've exited the hooks section
                    if current_hook:
                        hooks_list.append(current_hook)
                    current_hook = {}
                    in_hooks = False
                    # Parse this line as a regular key: value
                    key, val = line.split(':', 1)
                    frontmatter[key.strip()] = val.strip().strip('"\'')
        
        # Don't forget the last hook
        if in_hooks and current_hook:
            hooks_list.append(current_hook)
        
        if hooks_list:
            frontmatter['hooks'] = hooks_list
        
        return frontmatter
    
    except Exception as e:
        print(f"Warning: Failed to parse frontmatter in {file_path}: {e}", file=sys.stderr)
        return {}


def scan_hook_declarations(plugin_root):
    """Scan all .md files for hook declarations.
    
    Returns a list of dicts with: event, matcher, script, file_path
    """
    hooks = []
    
    # Directories to scan
    scan_dirs = [
        os.path.join(plugin_root, 'agents'),
        os.path.join(plugin_root, 'skills'),
        os.path.join(plugin_root, 'commands'),
    ]
    
    for scan_dir in scan_dirs:
        if not os.path.exists(scan_dir):
            continue
        
        # Find all .md files recursively
        md_files = glob.glob(os.path.join(scan_dir, '**', '*.md'), recursive=True)
        
        for md_file in md_files:
            frontmatter = parse_frontmatter(md_file)
            
            if 'hooks' not in frontmatter:
                continue
            
            # Process each hook declaration
            hooks_list = frontmatter['hooks']
            if not isinstance(hooks_list, list):
                print(f"Warning: hooks in {md_file} is not a list", file=sys.stderr)
                continue
            
            for hook in hooks_list:
                if not isinstance(hook, dict):
                    continue
                
                event = hook.get('event')
                matcher = hook.get('matcher')
                script = hook.get('script')
                
                if not all([event, matcher, script]):
                    print(f"Warning: Incomplete hook declaration in {md_file}: {hook}", file=sys.stderr)
                    continue
                
                hooks.append({
                    'event': event,
                    'matcher': matcher,
                    'script': script,
                    'file_path': md_file
                })
    
    return hooks


def load_hooks_json(plugin_root):
    """Load the current hooks/hooks.json file.
    
    Returns a dict with the full hooks structure, or creates a minimal one if missing.
    """
    hooks_file = os.path.join(plugin_root, 'hooks', 'hooks.json')
    
    if not os.path.exists(hooks_file):
        return {
            "description": "dark-factory plugin hooks — brain state management for agent orchestration",
            "hooks": {}
        }
    
    try:
        with open(hooks_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load hooks.json: {e}", file=sys.stderr)
        return {
            "description": "dark-factory plugin hooks — brain state management for agent orchestration",
            "hooks": {}
        }


def hook_exists(hooks_json, event, matcher, script):
    """Check if a hook already exists in hooks.json.
    
    Compares event, matcher, and script path (not the full command).
    """
    if event not in hooks_json.get('hooks', {}):
        return False
    
    event_hooks = hooks_json['hooks'][event]
    
    for matcher_entry in event_hooks:
        if matcher_entry.get('matcher') != matcher:
            continue
        
        # Check if this script command exists in the hooks list
        for hook in matcher_entry.get('hooks', []):
            if hook.get('type') != 'command':
                continue
            
            # Extract script path from command: bash "${CLAUDE_PLUGIN_ROOT}/path/to/script.sh"
            command = hook.get('command', '')
            if script in command:
                return True
    
    return False


def add_hook_to_json(hooks_json, event, matcher, script):
    """Add a new hook to the hooks.json structure if it doesn't already exist.
    
    Returns True if hook was added, False if it already existed.
    """
    if hook_exists(hooks_json, event, matcher, script):
        return False
    
    # Ensure event exists in hooks
    if event not in hooks_json['hooks']:
        hooks_json['hooks'][event] = []
    
    # Build the command with CLAUDE_PLUGIN_ROOT
    command = f'bash "${{CLAUDE_PLUGIN_ROOT}}/{script}"'
    
    # Check if this matcher already exists for this event
    matcher_entry = None
    for entry in hooks_json['hooks'][event]:
        if entry.get('matcher') == matcher:
            matcher_entry = entry
            break
    
    if matcher_entry is None:
        # Create new matcher entry
        matcher_entry = {
            'matcher': matcher,
            'hooks': [
                {
                    'type': 'command',
                    'command': command
                }
            ]
        }
        hooks_json['hooks'][event].append(matcher_entry)
    else:
        # Add to existing matcher entry
        matcher_entry['hooks'].append({
            'type': 'command',
            'command': command
        })
    
    return True


def save_hooks_json(plugin_root, hooks_json):
    """Save the updated hooks.json file."""
    hooks_file = os.path.join(plugin_root, 'hooks', 'hooks.json')
    
    # Ensure hooks directory exists
    os.makedirs(os.path.dirname(hooks_file), exist_ok=True)
    
    with open(hooks_file, 'w', encoding='utf-8') as f:
        json.dump(hooks_json, f, indent=2)
        f.write('\n')  # Add trailing newline


def main():
    """Main entry point."""
    plugin_root = get_plugin_root()
    
    # Scan for hook declarations
    declared_hooks = scan_hook_declarations(plugin_root)
    
    # Load current hooks.json
    hooks_json = load_hooks_json(plugin_root)
    
    # Add new hooks
    added_count = 0
    skipped_count = 0
    
    for hook in declared_hooks:
        if add_hook_to_json(hooks_json, hook['event'], hook['matcher'], hook['script']):
            added_count += 1
        else:
            skipped_count += 1
    
    # Save updated hooks.json
    save_hooks_json(plugin_root, hooks_json)
    
    # Print summary
    print(f"Added {added_count} hooks, skipped {skipped_count} duplicates")


if __name__ == '__main__':
    main()
