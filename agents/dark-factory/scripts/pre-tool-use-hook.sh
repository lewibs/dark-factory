#!/usr/bin/env bash
# pre-tool-use-hook.sh
# PreToolUse hook for the Agent tool.
# Injects brain.json context into the agent prompt and sets the current phase's *-running flag.
# Also captures start_ms for Agent/Skill tool calls into brain.json metrics section.
# Claude Code passes the hook input via stdin as JSON.
# Claude Code reads stdout to override the tool input.

set -euo pipefail

BRAIN_PATH="${DARK_FACTORY_WORK_DIR:-}/brain.json"

# pre-hook.no-brain: not a dark-factory session — pass through unchanged
if [ -z "${DARK_FACTORY_WORK_DIR:-}" ] || [ ! -f "$BRAIN_PATH" ]; then
  echo "pre-tool-use-hook | no-brain | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR:-unset}" >&2
  cat  # pass through stdin unchanged
  exit 0
fi

# Read the tool call input from stdin
TOOL_INPUT=$(cat)

TOOL_NAME=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_name // ""')

# ---------------------------------------------------------------------------
# pre-hook.metrics-capture: record start_ms for Agent or Skill tool calls
# ---------------------------------------------------------------------------
if [ "$TOOL_NAME" = "Agent" ] || [ "$TOOL_NAME" = "Skill" ]; then
  if [ "$TOOL_NAME" = "Agent" ]; then
    METRICS_KEY=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.subagent_type // "unknown"')
    if [ "$METRICS_KEY" = "null" ] || [ "$METRICS_KEY" = "unknown" ]; then
      # Fallback: try to extract agent name from prompt path reference (agents/<name>.md)
      METRICS_KEY=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.prompt // ""' \
        | grep -oP '(?<=agents/)[^/]+(?=\.md)' | head -1 || true)
      METRICS_KEY="${METRICS_KEY:-unknown}"
    fi
  else
    METRICS_KEY=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.skill // "unknown"')
  fi

  NOW_MS=$(date +%s%3N)
  echo "pre-tool-use-hook | metrics-capture | key=${METRICS_KEY} start_ms=${NOW_MS}" >&2

  METRICS_TMP=$(mktemp /tmp/brain-metrics-pre-XXXXXX.json)
  jq --arg key "$METRICS_KEY" --argjson now "$NOW_MS" \
    '.metrics[$key].start_ms = $now' "$BRAIN_PATH" > "$METRICS_TMP" \
    && mv "$METRICS_TMP" "$BRAIN_PATH"
fi

# pre-hook.set-phase-running: find the first phase that is not yet started
# and set its *-running=true
PHASE=$(jq -r '
  .phases | to_entries |
  map(select((.key | endswith("-complete")) and (.value == false))) |
  first | .key | rtrimstr("-complete") // empty
' "$BRAIN_PATH" 2>/dev/null || true)

if [ -n "$PHASE" ]; then
  echo "pre-tool-use-hook | set-phase-running | phase=${PHASE}" >&2
  PRE_TMP=$(mktemp /tmp/brain-pre-XXXXXX.json)
  jq ".phases[\"${PHASE}-running\"] = true" "$BRAIN_PATH" > "$PRE_TMP" \
    && mv "$PRE_TMP" "$BRAIN_PATH"
else
  echo "pre-tool-use-hook | set-phase-running | phase=none (all phases accounted for)" >&2
fi

# pre-hook.inject: inject brain context into the agent prompt
BRAIN_CONTEXT=$(jq -c '.' "$BRAIN_PATH")
ORIGINAL_PROMPT=$(printf '%s' "$TOOL_INPUT" | jq -r '.prompt // ""')
NEW_PROMPT="BRAIN STATE (read-only context — do not modify brain.json directly):
${BRAIN_CONTEXT}

${ORIGINAL_PROMPT}"

echo "pre-tool-use-hook | inject | brain_context_bytes=$(printf '%s' "$BRAIN_CONTEXT" | wc -c)" >&2

# Output the modified tool call — Claude Code reads hook stdout to override the tool input
printf '%s' "$TOOL_INPUT" | jq --arg p "$NEW_PROMPT" '.prompt = $p'
