#!/usr/bin/env bash
# post-tool-use-hook.sh
# PostToolUse hook for the Agent tool.
# Merges brain-patch.json into brain.json and marks the current phase complete.
# Also accumulates elapsed_ms, tokens, and runs for Agent/Skill tool calls.

set -euo pipefail

# Resolve DARK_FACTORY_WORK_DIR: prefer env var, fall back to pointer file.
# The env var is set by Claude Code when launched with it in the environment.
# The pointer file at /tmp/dark-factory-work-dir is written by dark-factory-agent
# immediately after creating brain.json; it provides a fallback for hook processes
# that inherit Claude Code's environment (where the LLM's `export` is invisible).
DARK_FACTORY_POINTER_FILE="/tmp/dark-factory-work-dir"
if [ -z "${DARK_FACTORY_WORK_DIR:-}" ] && [ -f "$DARK_FACTORY_POINTER_FILE" ]; then
  DARK_FACTORY_WORK_DIR=$(cat "$DARK_FACTORY_POINTER_FILE")
  echo "post-tool-use-hook | pointer-file | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR}" >&2
fi

BRAIN_PATH="${DARK_FACTORY_WORK_DIR:-}/brain.json"
PATCH_PATH="${DARK_FACTORY_WORK_DIR:-}/brain-patch.json"
BRAIN_LOCK="${BRAIN_PATH}.lock"

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
  (
    flock -x 200
    POST_TMP=$(mktemp /tmp/brain-post-XXXXXX.json)
    # Check if the patch contains notes or artifacts fields that require array-concat merge
    HAS_ARRAY_FIELDS=$(jq 'has("notes") or has("artifacts")' "$PATCH_PATH")
    if [ "$HAS_ARRAY_FIELDS" = "true" ]; then
      jq -s '
        (.[0].notes // []) + (.[1].notes // []) as $notes |
        ((.[0].artifacts.created // []) + (.[1].artifacts.created // [])) as $art_created |
        ((.[0].artifacts.modified // []) + (.[1].artifacts.modified // [])) as $art_modified |
        .[0] * .[1] |
        .notes = $notes |
        .artifacts.created = $art_created |
        .artifacts.modified = $art_modified
      ' "$BRAIN_PATH" "$PATCH_PATH" > "$POST_TMP" \
        && mv "$POST_TMP" "$BRAIN_PATH"
    else
      jq -s '.[0] * .[1]' "$BRAIN_PATH" "$PATCH_PATH" > "$POST_TMP" \
        && mv "$POST_TMP" "$BRAIN_PATH"
    fi
    rm -f "$PATCH_PATH"
  ) 200>"$BRAIN_LOCK"
else
  echo "post-tool-use-hook | no-patch | brain-patch.json not found, skipping merge" >&2
fi

# ---------------------------------------------------------------------------
# post-hook.metrics-accumulate: accumulate elapsed_ms + tokens + runs
# for Agent or Skill tool calls only.
# ---------------------------------------------------------------------------
TOOL_NAME=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_name // ""')

PHASE_AGENTS="feature-agent|debugger-agent|fix-flow-orchestrator|repair-agent|code-review-orchestrator-agent|update-documentation-agent|skill-update-agent|pr-agent"

if [ "$TOOL_NAME" = "Agent" ] || [ "$TOOL_NAME" = "Skill" ]; then
  if [ "$TOOL_NAME" = "Agent" ]; then
    METRICS_KEY=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.subagent_type // "unknown"')
    if [ "$METRICS_KEY" = "null" ] || [ "$METRICS_KEY" = "unknown" ]; then
      METRICS_KEY=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.prompt // ""' \
        | grep -oP '(?<=agents/)[^/]+(?=\.md)' | tail -1 || true)
      METRICS_KEY="${METRICS_KEY:-unknown}"
    fi
  else
    METRICS_KEY=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.skill // "unknown"')
  fi

  # Extract the short name after the last colon for metrics and phase-agent matching
  METRICS_KEY_SHORT=$(printf '%s' "$METRICS_KEY" | sed 's/.*://')

  NOW_MS=$(date +%s%3N)
  START_MS=$(jq --arg k "$METRICS_KEY_SHORT" '.metrics[$k].start_ms // 0' "$BRAIN_PATH")
  # If start_ms was absent it defaults to 0 — treat elapsed as 0 rather than computing
  # (NOW_MS - 0) which would yield an epoch-sized value.
  if [ "$START_MS" -eq 0 ]; then
    ELAPSED=0
  else
    ELAPSED=$(( NOW_MS - START_MS ))
  fi

  TOKENS=$(printf '%s' "$HOOK_INPUT" | jq \
    '(.tool_response.usage.input_tokens // 0) + (.tool_response.usage.output_tokens // 0)')

  echo "post-tool-use-hook | metrics-accumulate | key=${METRICS_KEY_SHORT} elapsed_ms=${ELAPSED} tokens=${TOKENS} runs=+1" >&2

  (
    flock -x 200
    METRICS_TMP=$(mktemp /tmp/brain-metrics-post-XXXXXX.json)
    jq --arg key "$METRICS_KEY_SHORT" --argjson elapsed "$ELAPSED" --argjson tokens "$TOKENS" '
      .metrics[$key].elapsed_ms = ((.metrics[$key].elapsed_ms // 0) + $elapsed) |
      .metrics[$key].tokens     = ((.metrics[$key].tokens     // 0) + $tokens)  |
      .metrics[$key].runs       = ((.metrics[$key].runs       // 0) + 1)        |
      del(.metrics[$key].start_ms)
    ' "$BRAIN_PATH" > "$METRICS_TMP" \
      && mv "$METRICS_TMP" "$BRAIN_PATH"
  ) 200>"$BRAIN_LOCK"

  # post-hook.set-phase-complete: mark the currently-running phase complete,
  # but only when the completing agent is a top-level orchestration phase agent.
  if [[ "$METRICS_KEY_SHORT" =~ ^($PHASE_AGENTS)$ ]]; then
    (
      flock -x 200
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
    ) 200>"$BRAIN_LOCK"
  else
    echo "post-tool-use-hook | set-phase-complete | skipped (agent=${METRICS_KEY_SHORT} not a phase agent)" >&2
  fi
else
  # Non-Agent/Skill tool: still check for phase completion (shouldn't normally happen, but keep safe)
  echo "post-tool-use-hook | set-phase-complete | skipped (tool=${TOOL_NAME} not Agent or Skill)" >&2
fi
