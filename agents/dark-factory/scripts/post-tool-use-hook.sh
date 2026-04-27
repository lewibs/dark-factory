#!/usr/bin/env bash
# post-tool-use-hook.sh
# PostToolUse hook for the Agent tool.
# Merges brain-patch.json into brain.json and marks the current phase complete.

set -euo pipefail

BRAIN_PATH="${DARK_FACTORY_WORK_DIR:-}/brain.json"
PATCH_PATH="${DARK_FACTORY_WORK_DIR:-}/brain-patch.json"

# post-hook.no-brain: not a dark-factory session — exit silently
if [ -z "${DARK_FACTORY_WORK_DIR:-}" ] || [ ! -f "$BRAIN_PATH" ]; then
  echo "post-tool-use-hook | no-brain | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR:-unset}" >&2
  exit 0
fi

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
