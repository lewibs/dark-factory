#!/usr/bin/env bash
# post-tool-use-hook.sh
# PostToolUse hook for the Agent tool.
# Merges brain-patch.json into brain.json and marks the current phase complete.
# Also accumulates elapsed_ms, tokens, and runs for Agent/Skill tool calls.

set -euo pipefail

BRAIN_PATH="${DARK_FACTORY_WORK_DIR:-}/brain.json"
PATCH_PATH="${DARK_FACTORY_WORK_DIR:-}/brain-patch.json"

# post-hook.no-brain: not a dark-factory session — exit silently
if [ -z "${DARK_FACTORY_WORK_DIR:-}" ] || [ ! -f "$BRAIN_PATH" ]; then
  echo "post-tool-use-hook | no-brain | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR:-unset}" >&2
  exit 0
fi

# Read the tool call input from stdin (saved so we can use it for both merge and metrics)
HOOK_INPUT=$(cat)

# post-hook.merge-patch: merge brain-patch.json into brain.json if it exists
if [ -f "$PATCH_PATH" ]; then
  PATCH_CONTENTS=$(jq -c '.' "$PATCH_PATH")
  echo "post-tool-use-hook | merge-patch | patch=${PATCH_CONTENTS}" >&2
  POST_TMP=$(mktemp /tmp/brain-post-XXXXXX.json)
  jq -s '.[0] * .[1]' "$BRAIN_PATH" "$PATCH_PATH" > "$POST_TMP" \
    && mv "$POST_TMP" "$BRAIN_PATH"
  rm -f "$PATCH_PATH"
else
  echo "post-tool-use-hook | no-patch | brain-patch.json not found, skipping merge" >&2
fi

# post-hook.set-phase-complete: find the currently-running phase and mark it complete
RUNNING_PHASE=$(jq -r '
  .phases | to_entries |
  map(select((.key | endswith("-running")) and (.value == true))) |
  first | .key // empty
' "$BRAIN_PATH" 2>/dev/null || true)

if [ -n "$RUNNING_PHASE" ]; then
  COMPLETE_PHASE="${RUNNING_PHASE%-running}-complete"
  echo "post-tool-use-hook | set-phase-complete | running=${RUNNING_PHASE} complete=${COMPLETE_PHASE}" >&2
  POST_TMP2=$(mktemp /tmp/brain-post-XXXXXX.json)
  jq ".phases[\"${RUNNING_PHASE}\"] = false | .phases[\"${COMPLETE_PHASE}\"] = true" \
    "$BRAIN_PATH" > "$POST_TMP2" \
    && mv "$POST_TMP2" "$BRAIN_PATH"
else
  echo "post-tool-use-hook | set-phase-complete | no running phase found" >&2
fi

# ---------------------------------------------------------------------------
# post-hook.metrics-accumulate: accumulate elapsed_ms + tokens + runs
# for Agent or Skill tool calls only.
# ---------------------------------------------------------------------------
TOOL_NAME=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_name // ""')

if [ "$TOOL_NAME" = "Agent" ] || [ "$TOOL_NAME" = "Skill" ]; then
  if [ "$TOOL_NAME" = "Agent" ]; then
    METRICS_KEY=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.subagent_type // "unknown"')
    if [ "$METRICS_KEY" = "null" ] || [ "$METRICS_KEY" = "unknown" ]; then
      METRICS_KEY=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.prompt // ""' \
        | grep -oP '(?<=agents/)[^/]+(?=\.md)' | head -1 || true)
      METRICS_KEY="${METRICS_KEY:-unknown}"
    fi
  else
    METRICS_KEY=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.skill // "unknown"')
  fi

  NOW_MS=$(date +%s%3N)
  START_MS=$(jq --arg k "$METRICS_KEY" '.metrics[$k].start_ms // 0' "$BRAIN_PATH")
  # If start_ms was absent it defaults to 0 — treat elapsed as 0 rather than computing
  # (NOW_MS - 0) which would yield an epoch-sized value.
  if [ "$START_MS" -eq 0 ]; then
    ELAPSED=0
  else
    ELAPSED=$(( NOW_MS - START_MS ))
  fi

  TOKENS=$(printf '%s' "$HOOK_INPUT" | jq \
    '(.tool_response.usage.input_tokens // 0) + (.tool_response.usage.output_tokens // 0)')

  echo "post-tool-use-hook | metrics-accumulate | key=${METRICS_KEY} elapsed_ms=${ELAPSED} tokens=${TOKENS} runs=+1" >&2

  METRICS_TMP=$(mktemp /tmp/brain-metrics-post-XXXXXX.json)
  jq --arg key "$METRICS_KEY" --argjson elapsed "$ELAPSED" --argjson tokens "$TOKENS" '
    .metrics[$key].elapsed_ms = ((.metrics[$key].elapsed_ms // 0) + $elapsed) |
    .metrics[$key].tokens     = ((.metrics[$key].tokens     // 0) + $tokens)  |
    .metrics[$key].runs       = ((.metrics[$key].runs       // 0) + 1)        |
    del(.metrics[$key].start_ms)
  ' "$BRAIN_PATH" > "$METRICS_TMP" \
    && mv "$METRICS_TMP" "$BRAIN_PATH"
fi
