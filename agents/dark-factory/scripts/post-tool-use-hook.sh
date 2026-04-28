#!/usr/bin/env bash
# post-tool-use-hook.sh
# PostToolUse hook for the Agent tool.
# Merges brain-patch.json into brain.json and marks the current phase complete.
# Also accumulates elapsed_ms, tokens, and runs for Agent/Skill tool calls.

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
  echo "post-tool-use-hook | pointer-file | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR}" >&2
fi

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
  _TMP_FILES+=("$POST_TMP")
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
  _TMP_FILES+=("$POST_TMP2")
  jq ".phases[\"${RUNNING_PHASE}\"] = false | .phases[\"${COMPLETE_PHASE}\"] = true" \
    "$BRAIN_PATH" > "$POST_TMP2" \
    && mv "$POST_TMP2" "$BRAIN_PATH"
else
  echo "post-tool-use-hook | set-phase-complete | no running phase found" >&2
fi

# post-hook.trigger-docs-update: if the worker phase just completed, run the
# documentation update agent synchronously so docs are written before code review
# and the PR are opened.
if [ "${RUNNING_PHASE:-}" = "worker-running" ]; then
  PLAN_FILE_PATH=$(jq -r '.planFilePath // empty' "$BRAIN_PATH" 2>/dev/null || true)
  WORK_DIR="${DARK_FACTORY_WORK_DIR}"
  DOC_AGENT_PATH="${WORK_DIR}/agents/documentation/agents/update-documentation-agent.md"
  if [ -f "$DOC_AGENT_PATH" ]; then
    DOC_AGENT_INSTRUCTIONS=$(cat "$DOC_AGENT_PATH")

    # Use planFilePath when available; fall back to taskDescription so the docs
    # agent always has meaningful context.
    if [ -n "$PLAN_FILE_PATH" ]; then
      DOC_CONTEXT="Plan file path: ${PLAN_FILE_PATH}"
    else
      TASK_DESCRIPTION=$(jq -r '.taskDescription // ""' "$BRAIN_PATH" 2>/dev/null || true)
      DOC_CONTEXT="Task description (no plan file): ${TASK_DESCRIPTION}"
    fi

    DOC_PROMPT="${DOC_AGENT_INSTRUCTIONS}

${DOC_CONTEXT}"
    LOG_FILE="/tmp/docs-update-$$.log"

    # Mark docs phase running before launching
    DOCS_TMP=$(mktemp /tmp/brain-docs-XXXXXX.json)
    _TMP_FILES+=("$DOCS_TMP")
    jq '.phases["docs-running"] = true' "$BRAIN_PATH" > "$DOCS_TMP" \
      && mv "$DOCS_TMP" "$BRAIN_PATH"

    # Run synchronously. Unset DARK_FACTORY_WORK_DIR to prevent hook re-entrancy
    # inside the docs subprocess; use --model to match the agent's declared model.
    (
      cd "$WORK_DIR"
      unset DARK_FACTORY_WORK_DIR
      claude --model claude-sonnet-4-6 --allowedTools "Read,Grep,Glob,Write,Edit,Bash" -p "$DOC_PROMPT" >"$LOG_FILE" 2>&1
    )
    DOC_EXIT=$?

    # Mark docs phase complete regardless of exit code (non-fatal)
    DOCS_TMP2=$(mktemp /tmp/brain-docs-XXXXXX.json)
    _TMP_FILES+=("$DOCS_TMP2")
    jq '.phases["docs-running"] = false | .phases["docs-complete"] = true' "$BRAIN_PATH" > "$DOCS_TMP2" \
      && mv "$DOCS_TMP2" "$BRAIN_PATH"

    echo "post-tool-use-hook | trigger-docs-update | exit=${DOC_EXIT} log=${LOG_FILE}" >&2
  else
    echo "post-tool-use-hook | trigger-docs-update | doc-agent not found at ${DOC_AGENT_PATH}, skipping" >&2
  fi
fi

# ---------------------------------------------------------------------------
# post-hook.metrics-accumulate: accumulate elapsed_ms + tokens + runs
# for Agent or Skill tool calls only.
# ---------------------------------------------------------------------------
TOOL_NAME=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_name // ""')

if [ "$TOOL_NAME" = "Agent" ] || [ "$TOOL_NAME" = "Skill" ]; then
  METRICS_KEY=$(bash "$HOOK_DIR/extract-metrics-key.sh" "$TOOL_NAME" "$HOOK_INPUT")

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
  _TMP_FILES+=("$METRICS_TMP")
  jq --arg key "$METRICS_KEY" --argjson elapsed "$ELAPSED" --argjson tokens "$TOKENS" '
    .metrics[$key].elapsed_ms = ((.metrics[$key].elapsed_ms // 0) + $elapsed) |
    .metrics[$key].tokens     = ((.metrics[$key].tokens     // 0) + $tokens)  |
    .metrics[$key].runs       = ((.metrics[$key].runs       // 0) + 1)        |
    del(.metrics[$key].start_ms)
  ' "$BRAIN_PATH" > "$METRICS_TMP" \
    && mv "$METRICS_TMP" "$BRAIN_PATH"
fi
