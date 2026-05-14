#!/usr/bin/env bash
# pre-tool-use-hook.sh
# PreToolUse hook for the Agent tool.
# Injects brain.json context into the agent prompt and sets the current phase's *-running flag.
# Also captures start_ms for Agent/Skill tool calls into brain.json metrics section.
# Claude Code passes the hook input via stdin as JSON.
# Claude Code reads stdout to override the tool input.

set -euo pipefail

# Resolve DARK_FACTORY_WORK_DIR: prefer env var, fall back to pointer file.
# The env var is set by Claude Code when launched with it in the environment.
# The pointer file at /tmp/dark-factory-work-dir is written by dark-factory-agent
# immediately after creating brain.json; it provides a fallback for hook processes
# that inherit Claude Code's environment (where the LLM's `export` is invisible).
DARK_FACTORY_POINTER_FILE="/tmp/dark-factory-work-dir"
if [ -z "${DARK_FACTORY_WORK_DIR:-}" ] && [ -f "$DARK_FACTORY_POINTER_FILE" ]; then
  DARK_FACTORY_WORK_DIR=$(cat "$DARK_FACTORY_POINTER_FILE")
  echo "pre-tool-use-hook | pointer-file | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR}" >&2
fi

BRAIN_PATH="${DARK_FACTORY_WORK_DIR:-}/brain.json"
BRAIN_LOCK="${BRAIN_PATH}.lock"

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
        | grep -oP '(?<=agents/)[^/]+(?=\.md)' | tail -1 || true)
      METRICS_KEY="${METRICS_KEY:-unknown}"
    fi
  else
    METRICS_KEY=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.skill // "unknown"')
  fi

  NOW_MS=$(date +%s%3N)
  echo "pre-tool-use-hook | metrics-capture | key=${METRICS_KEY} start_ms=${NOW_MS}" >&2

  (
    flock -x 200
    METRICS_TMP=$(mktemp /tmp/brain-metrics-pre-XXXXXX.json)
    jq --arg key "$METRICS_KEY" --argjson now "$NOW_MS" \
      '.metrics[$key].start_ms = $now' "$BRAIN_PATH" > "$METRICS_TMP" \
      && mv "$METRICS_TMP" "$BRAIN_PATH"
  ) 200>"$BRAIN_LOCK"
fi

# pre-hook.set-phase-running: find the first phase that is not yet started
# and set its *-running=true — only for top-level orchestration phase agents
PHASE_AGENTS="feature-agent|debugger-agent|repair-agent|code-review-orchestrator-agent|update-documentation-agent|skill-update-agent|pr-agent"

# Extract agent name for phase-agent check (TOOL_NAME and TOOL_INPUT already set above)
PHASE_AGENT_NAME=""
if [ "$TOOL_NAME" = "Agent" ]; then
  PHASE_AGENT_NAME=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.subagent_type // ""')
fi

if [[ "$PHASE_AGENT_NAME" =~ ^($PHASE_AGENTS)$ ]]; then
  PHASE=$(jq -r '
    .phases | to_entries |
    map(select((.key | endswith("-complete")) and (.value == false))) |
    first | .key | rtrimstr("-complete") // empty
  ' "$BRAIN_PATH" 2>/dev/null || true)

  if [ -n "$PHASE" ]; then
    echo "pre-tool-use-hook | set-phase-running | phase=${PHASE}" >&2
    (
      flock -x 200
      PRE_TMP=$(mktemp /tmp/brain-pre-XXXXXX.json)
      jq ".phases[\"${PHASE}-running\"] = true" "$BRAIN_PATH" > "$PRE_TMP" \
        && mv "$PRE_TMP" "$BRAIN_PATH"
    ) 200>"$BRAIN_LOCK"
  else
    echo "pre-tool-use-hook | set-phase-running | phase=none (all phases accounted for)" >&2
  fi
else
  echo "pre-tool-use-hook | set-phase-running | skipped (agent=${PHASE_AGENT_NAME} not a phase agent)" >&2
fi

# pre-hook.inject: inject brain context into the agent prompt
BRAIN_CONTEXT=$(jq -c '.' "$BRAIN_PATH")
CURRENT_PROMPT=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.prompt // .prompt // ""')

NOTES_JSON=$(jq -c '.notes // []' "$BRAIN_PATH")
NOTES_COUNT=$(printf '%s' "$NOTES_JSON" | jq 'length')
if [ "$NOTES_COUNT" -gt 0 ]; then
  NOTES_BLOCK=$(printf '%s' "$NOTES_JSON" | jq -r '.[] | "- " + .')
  NOTES_HEADER="HANDOFF NOTES FROM PRIOR AGENTS:\n${NOTES_BLOCK}\n\n"
else
  NOTES_HEADER=""
fi

NEW_PROMPT="${NOTES_HEADER}BRAIN STATE (read-only context — do not modify brain.json directly):
${BRAIN_CONTEXT}

${CURRENT_PROMPT}"

echo "pre-tool-use-hook | inject | brain_context_bytes=$(printf '%s' "$BRAIN_CONTEXT" | wc -c)" >&2

# Output the modified tool call — Claude Code reads hook stdout to override the tool input
printf '%s' "$TOOL_INPUT" | jq --arg p "$NEW_PROMPT" 'if .tool_input.prompt != null then .tool_input.prompt = $p else .prompt = $p end'
