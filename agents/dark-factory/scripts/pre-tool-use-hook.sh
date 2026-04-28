#!/usr/bin/env bash
# pre-tool-use-hook.sh
# PreToolUse hook for the Agent tool.
# Injects brain.json context into the agent prompt and sets the current phase's *-running flag.
# Also captures start_ms for Agent/Skill tool calls into brain.json metrics section.
# Claude Code passes the hook input via stdin as JSON.
# Claude Code reads stdout to override the tool input.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Temp file cleanup: collect paths and remove on exit.
_TMP_FILES=()
_cleanup_tmp() { rm -f "${_TMP_FILES[@]}" 2>/dev/null || true; }
trap _cleanup_tmp EXIT

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
  METRICS_KEY=$(bash "$HOOK_DIR/extract-metrics-key.sh" "$TOOL_NAME" "$TOOL_INPUT")

  NOW_MS=$(date +%s%3N)
  echo "pre-tool-use-hook | metrics-capture | key=${METRICS_KEY} start_ms=${NOW_MS}" >&2

  METRICS_TMP=$(mktemp /tmp/brain-metrics-pre-XXXXXX.json)
  _TMP_FILES+=("$METRICS_TMP")
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
  _TMP_FILES+=("$PRE_TMP")
  jq ".phases[\"${PHASE}-running\"] = true" "$BRAIN_PATH" > "$PRE_TMP" \
    && mv "$PRE_TMP" "$BRAIN_PATH"
else
  echo "pre-tool-use-hook | set-phase-running | phase=none (all phases accounted for)" >&2
fi

# ---------------------------------------------------------------------------
# pre-hook.checklist-inject: inject agent checklist into prompt (Agent tool only)
# ---------------------------------------------------------------------------
AGENT_NAME=""
if [ "$TOOL_NAME" = "Agent" ]; then
  AGENT_NAME=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.subagent_type // ""')
fi

declare -A AGENT_CHECKLISTS
AGENT_CHECKLISTS["dark-factory-agent"]="Classify task|Prep work dir|Run worker agent|Code review|Update skills|Open PR|Cleanup"
AGENT_CHECKLISTS["feature-agent"]="Plan feature|Get plan approval|Execute plan"
AGENT_CHECKLISTS["execution-agent"]="Build skeleton|Write tests|Implement flows"
AGENT_CHECKLISTS["skeleton-agent"]="Read plan|Build files checklist|Create skeleton files"
AGENT_CHECKLISTS["testing-agent"]="Read plan|Build flows checklist|Write failing tests"
AGENT_CHECKLISTS["implementation-agent"]="Read plan|Implement each flow|Run tests"
AGENT_CHECKLISTS["planning-agent"]="Spawn draft-plan sub-agent|Run mermaid phase|Run flows phase (one at a time)|Return planPath"
AGENT_CHECKLISTS["sub-planning-agent"]="Research phase context|Update plan file|Run mermaid script (mermaid phase only)|Return structured output"
AGENT_CHECKLISTS["code-review-orchestrator-agent"]="Run high-level review|Run low-level review|Resolve issues"
AGENT_CHECKLISTS["high-level-review-agent"]="Read plan|Review code structure|Append issues"
AGENT_CHECKLISTS["low-level-review-agent"]="Review functions|Check edge cases|Append issues"
AGENT_CHECKLISTS["resolver-agent"]="Read issues|Apply fixes|Check off resolved items"
AGENT_CHECKLISTS["debugger-agent"]="Reproduce bug|Identify root cause|Apply fix|Write audit log"
AGENT_CHECKLISTS["pr-agent"]="Open PR|Wait for CI|Address review comments"
AGENT_CHECKLISTS["update-documentation-agent"]="Identify affected docs|Update stale content|Add new information"
AGENT_CHECKLISTS["skill-update-agent"]="Review completed work|Identify patterns|Write skill files"
AGENT_CHECKLISTS["repair-implementation-agent"]="Apply fix|Run tests|Return success"
AGENT_CHECKLISTS["fix-flow-orchestrator"]="Understand system|Generate scripts|Run flow|Debug failures|Ship PR"

REPO_ROOT="$(cd "$HOOK_DIR/../../.." && pwd)"
CHECKLIST_SCRIPT="$REPO_ROOT/scripts/generate_checklist.sh"

if [[ -n "$AGENT_NAME" ]] && [[ -n "${AGENT_CHECKLISTS[$AGENT_NAME]:-}" ]]; then
  echo "pre-tool-use-hook | checklist-inject | agent=${AGENT_NAME}" >&2
  IFS='|' read -ra ITEMS <<< "${AGENT_CHECKLISTS[$AGENT_NAME]}"
  CHECKLIST_JSON=$(bash "$CHECKLIST_SCRIPT" "${ITEMS[@]}")
  CHECKLIST_INSTRUCTION="At the start of your work, call TodoWrite with this exact body:
${CHECKLIST_JSON}
Then work through each item, marking it in_progress when you start and completed when done."
  ORIGINAL_PROMPT=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.prompt // ""')
  NEW_PROMPT="${CHECKLIST_INSTRUCTION}

${ORIGINAL_PROMPT}"
  TOOL_INPUT=$(printf '%s' "$TOOL_INPUT" | jq --arg p "$NEW_PROMPT" '.tool_input.prompt = $p')
elif [ "$TOOL_NAME" = "Agent" ]; then
  echo "pre-tool-use-hook | checklist-skip | agent=${AGENT_NAME}" >&2
fi

# pre-hook.inject: inject brain context into the agent prompt (Agent tool only).
# Skill tool calls have no prompt field in tool_input; injecting into a stray
# top-level .prompt key is silently ignored by the Skill framework, so skip it.
if [ "$TOOL_NAME" = "Agent" ]; then
  # NOTE: TOOL_INPUT may already have the checklist prepended by the block above.
  # We read the current prompt from the (possibly already modified) TOOL_INPUT so
  # that we prepend brain context to the full prompt, not just the original prompt.
  BRAIN_CONTEXT=$(jq -c '.' "$BRAIN_PATH")
  CURRENT_PROMPT=$(printf '%s' "$TOOL_INPUT" | jq -r '.tool_input.prompt // ""')
  NEW_PROMPT="BRAIN STATE (read-only context — do not modify brain.json directly):
${BRAIN_CONTEXT}

${CURRENT_PROMPT}"

  echo "pre-tool-use-hook | inject | brain_context_bytes=$(printf '%s' "$BRAIN_CONTEXT" | wc -c)" >&2

  # Output the modified tool call — Claude Code reads hook stdout to override the tool input
  printf '%s' "$TOOL_INPUT" | jq --arg p "$NEW_PROMPT" '.tool_input.prompt = $p'
else
  echo "pre-tool-use-hook | inject-skip | tool=${TOOL_NAME} has no prompt field, passing through" >&2
  printf '%s' "$TOOL_INPUT"
fi
