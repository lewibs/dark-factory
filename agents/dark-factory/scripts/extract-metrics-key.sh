#!/usr/bin/env bash
# extract-metrics-key.sh <tool_name> <json_string>
# Prints the metrics key for a given tool call.
# Used by both pre-tool-use-hook.sh and post-tool-use-hook.sh to avoid duplication.
# Portable: uses sed instead of grep -oP (which is GNU-only).

set -euo pipefail

TOOL_NAME="$1"
JSON="$2"

if [ "$TOOL_NAME" = "Agent" ]; then
  KEY=$(printf '%s' "$JSON" | jq -r '.tool_input.subagent_type // "unknown"')
  if [ "$KEY" = "null" ] || [ "$KEY" = "unknown" ]; then
    # Fallback: extract agent name from a path reference like agents/<name>.md in the prompt
    KEY=$(printf '%s' "$JSON" | jq -r '.tool_input.prompt // ""' \
      | sed -n 's|.*agents/\([^/]*\)\.md.*|\1|p' | head -1 || true)
    KEY="${KEY:-unknown}"
  fi
else
  KEY=$(printf '%s' "$JSON" | jq -r '.tool_input.skill // "unknown"')
fi

printf '%s' "$KEY"
