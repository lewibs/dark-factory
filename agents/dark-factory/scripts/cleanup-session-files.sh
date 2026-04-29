#!/usr/bin/env bash
# cleanup-session-files.sh
# Cleans up transient session files that were created during a dark-factory run.
# This script is called by the Stop hook to ensure session files are never
# accidentally committed to git, even if the manufacturing process is interrupted.
#
# Files cleaned up:
#   - brain.json (agent state context)
#   - brain.json.lock (flock file)
#   - brain-patch.json (agent output patch)
#   - flows-state.json (flow approval state)
#   - /tmp/dark-factory-work-dir (pointer to work dir)
#
# This is deterministic and automatic — no manual intervention required.
# Failures are logged as warnings but do not cause the hook to fail (exit 0).

set -euo pipefail

# Resolve the work directory: prefer env var, fall back to pointer file
DARK_FACTORY_POINTER_FILE="/tmp/dark-factory-work-dir"
WORK_DIR="${DARK_FACTORY_WORK_DIR:-}"

if [ -z "$WORK_DIR" ] && [ -f "$DARK_FACTORY_POINTER_FILE" ]; then
  WORK_DIR=$(cat "$DARK_FACTORY_POINTER_FILE")
  echo "cleanup-session-files | pointer-file | DARK_FACTORY_WORK_DIR=${WORK_DIR}" >&2
fi

# If no work dir found, nothing to clean up
if [ -z "$WORK_DIR" ]; then
  echo "cleanup-session-files | no-work-dir | skipping session file cleanup" >&2
  exit 0
fi

# Array of session files to clean up (relative to WORK_DIR or absolute paths)
SESSION_FILES=(
  "$WORK_DIR/brain.json"
  "$WORK_DIR/brain.json.lock"
  "$WORK_DIR/brain-patch.json"
  "$WORK_DIR/flows-state.json"
  "/tmp/dark-factory-work-dir"
)

# Clean up each file
for file in "${SESSION_FILES[@]}"; do
  if [ -f "$file" ]; then
    rm -f "$file" 2>/dev/null && \
      echo "cleanup-session-files | deleted | $file" >&2 || \
      echo "WARNING: cleanup-session-files | failed to delete | $file" >&2
  fi
done

exit 0
