#!/usr/bin/env bash
# phase-order-enforcement-hook.sh
# PreToolUse / PreAgentUse hook that enforces sequential phase execution for
# agents with strictly-ordered numbered flows (1 → 2 → 3 ... N).
# The hook prevents an agent from advancing to a later phase if earlier phases
# have not yet completed.
# Claude Code passes the hook input via stdin as JSON.
#
# Flow: check-phase-order, mark-phase-complete

set -euo pipefail

LOG_FILE="${DARK_FACTORY_WORK_DIR:-/tmp}/phase-order-enforcement.log"

log() {
  echo "phase-order-enforcement-hook | $*" >&2
  echo "$(date -Iseconds) phase-order-enforcement-hook | $*" >> "$LOG_FILE" 2>/dev/null || true
}

# Resolve DARK_FACTORY_WORK_DIR: prefer env var, fall back to pointer file.
DARK_FACTORY_POINTER_FILE="/tmp/dark-factory-work-dir"
if [ -z "${DARK_FACTORY_WORK_DIR:-}" ] && [ -f "$DARK_FACTORY_POINTER_FILE" ]; then
  DARK_FACTORY_WORK_DIR=$(cat "$DARK_FACTORY_POINTER_FILE")
  log "pointer-file | DARK_FACTORY_WORK_DIR=${DARK_FACTORY_WORK_DIR}"
fi

BRAIN_PATH="${DARK_FACTORY_WORK_DIR:-}/brain.json"
BRAIN_LOCK="${BRAIN_PATH}.lock"

# Phase map: agents with strictly ordered numbered phases
# Maps agent name -> number of phases (informational; we only check completedPhases array)
# Per plan (docs/plans/2026-05-01-phase-order-enforcement-hook.md):
# - dark-factory-agent: 7 phases (numbered workflow)
# - update-documentation-agent: 3 phases (numbered workflow)
# - fix-flow-orchestrator: 3 phases (numbered workflow)
# - planning-agent: 1 phase (non-numbered, mentioned for completeness)
# - execution-agent: variable phases per flow (mentioned in plan but not enforced here)
declare -A PHASE_MAP
PHASE_MAP["dark-factory-agent"]=7
PHASE_MAP["update-documentation-agent"]=3
PHASE_MAP["fix-flow-orchestrator"]=3

# ---------------------------------------------------------------------------
# checkPhaseOrder
# Reads agentName and currentPhase from hook input JSON.
# Outputs JSON to stdout: { allowed: bool, reason: string|null }
# Exits 0 if allowed, 2 if blocked (SubagentStop).
# ---------------------------------------------------------------------------
checkPhaseOrder() {
  local agent_name="$1"
  local current_phase="$2"

  log "check-phase-order | agent=${agent_name} currentPhase=${current_phase}"

  # If agent not in phase map, allow
  if [ -z "${PHASE_MAP[$agent_name]+_}" ]; then
    log "check-phase-order.allowed | agent=${agent_name} not in phase map"
    printf '{"allowed":true}\n'
    exit 0
  fi

  # Phase 1 is always allowed (no prerequisites)
  if [ "$current_phase" -le 1 ]; then
    log "check-phase-order.allowed | agent=${agent_name} phase=1 no prerequisites"
    printf '{"allowed":true}\n'
    exit 0
  fi

  # Read completedPhases from brain.json
  if [ ! -f "$BRAIN_PATH" ]; then
    log "check-phase-order.allowed | no brain.json found, allowing"
    printf '{"allowed":true}\n'
    exit 0
  fi

  local completed_phases_json
  completed_phases_json=$(jq -r '.phases.completedPhases // [] | @json' "$BRAIN_PATH" 2>/dev/null || echo "[]")

  log "check-phase-order | completedPhases=${completed_phases_json}"

  # Find incomplete prerequisite phases: phases 1..(currentPhase-1) not in completedPhases
  local required_phase
  local incomplete_phases="[]"
  for (( required_phase=1; required_phase < current_phase; required_phase++ )); do
    local is_complete
    is_complete=$(printf '%s' "$completed_phases_json" | jq --argjson p "$required_phase" 'map(select(. == $p)) | length > 0')
    if [ "$is_complete" = "false" ]; then
      incomplete_phases=$(printf '%s' "$incomplete_phases" | jq --argjson p "$required_phase" '. + [$p]')
    fi
  done

  local num_incomplete
  num_incomplete=$(printf '%s' "$incomplete_phases" | jq 'length')

  if [ "$num_incomplete" -eq 0 ]; then
    log "check-phase-order.allowed | agent=${agent_name} phase=${current_phase} all prerequisites complete"
    printf '{"allowed":true}\n'
    exit 0
  else
    local incomplete_list
    incomplete_list=$(printf '%s' "$incomplete_phases" | jq -r 'join(", ")')
    local reason="Phase order violation in ${agent_name}: cannot execute phase ${current_phase} until phases ${incomplete_list} are complete."
    log "check-phase-order.blocked | agent=${agent_name} phase=${current_phase} incomplete=${incomplete_list}"
    # Use jq to properly escape the reason string in JSON output; exit 0 for normal hook completion
    printf '%s\n' "$(jq -n --arg reason "$reason" '{allowed: false, reason: $reason}')"
    exit 0
  fi
}

# ---------------------------------------------------------------------------
# markPhaseComplete
# Accepts agentName and phaseNumber from hook input JSON.
# Appends phaseNumber to completedPhases in brain.json using flock.
# Outputs JSON: { updated: bool, newCompletedPhases: [...] } or { updated: false, error: string }
# ---------------------------------------------------------------------------
markPhaseComplete() {
  local agent_name="$1"
  local phase_number="$2"

  log "mark-phase-complete | agent=${agent_name} phaseNumber=${phase_number}"

  if [ ! -f "$BRAIN_PATH" ]; then
    log "mark-phase-complete.error | brain.json not found at ${BRAIN_PATH}"
    printf '{"updated":false,"error":"brain.json not found at %s"}\n' "$BRAIN_PATH"
    exit 0
  fi

  # Check if brain.json is writable before attempting write
  if [ ! -w "$BRAIN_PATH" ]; then
    log "mark-phase-complete.error | agent=${agent_name} phase=${phase_number} brain.json not writable"
    printf '{"updated":false,"error":"brain.json is not writable: %s"}\n' "$BRAIN_PATH"
    exit 0
  fi

  # Try to write with flock using a temp file + atomic mv
  local tmp_file
  tmp_file=$(mktemp /tmp/brain-phase-XXXXXX.json)

  local write_status="failed"
  (
    flock -x 200
    if jq --argjson p "$phase_number" '
      .phases.completedPhases = ((.phases.completedPhases // []) + [$p] | unique | sort)
    ' "$BRAIN_PATH" > "$tmp_file" 2>/dev/null; then
      if mv "$tmp_file" "$BRAIN_PATH" 2>/dev/null; then
        true
      fi
    fi
  ) 200>"$BRAIN_LOCK" && write_status="ok" || write_status="failed"

  # Clean up tmp if still present
  rm -f "$tmp_file" 2>/dev/null || true

  # Re-read to get updated completedPhases and verify write succeeded
  if [ "$write_status" = "ok" ] && [ -f "$BRAIN_PATH" ]; then
    local new_completed
    new_completed=$(jq '.phases.completedPhases // []' "$BRAIN_PATH" 2>/dev/null || echo "[]")
    local has_phase
    has_phase=$(printf '%s' "$new_completed" | jq --argjson p "$phase_number" 'map(select(. == $p)) | length > 0')
    if [ "$has_phase" = "true" ]; then
      log "mark-phase-complete.success | agent=${agent_name} phase=${phase_number} newCompletedPhases=${new_completed}"
      printf '{"updated":true,"newCompletedPhases":%s}\n' "$new_completed"
      exit 0
    fi
  fi

  log "mark-phase-complete.error | agent=${agent_name} phase=${phase_number} write failed"
  printf '{"updated":false,"error":"Failed to write brain.json: write or permission error"}\n'
  exit 0
}

# ---------------------------------------------------------------------------
# main
# Reads stdin JSON, dispatches to checkPhaseOrder or markPhaseComplete.
# ---------------------------------------------------------------------------
main() {
  local tool_input
  tool_input=$(cat)

  local tool_name
  tool_name=$(printf '%s' "$tool_input" | jq -r '.tool_name // ""')

  local command_field
  command_field=$(printf '%s' "$tool_input" | jq -r '.tool_input.command // ""')

  # Dispatch to mark-phase-complete if command field is set
  if [ "$command_field" = "mark-phase-complete" ]; then
    local agent_name phase_number
    agent_name=$(printf '%s' "$tool_input" | jq -r '.tool_input.agentName // ""')
    phase_number=$(printf '%s' "$tool_input" | jq -r '.tool_input.phaseNumber // 0')

    if [ -z "$agent_name" ] || [ "$phase_number" -eq 0 ]; then
      log "mark-phase-complete.error | missing agentName or phaseNumber"
      printf '{"updated":false,"error":"missing agentName or phaseNumber"}\n'
      exit 0
    fi

    markPhaseComplete "$agent_name" "$phase_number"
    return
  fi

  # Default: check-phase-order
  local agent_name current_phase
  agent_name=$(printf '%s' "$tool_input" | jq -r '.tool_input.agentName // ""')
  current_phase=$(printf '%s' "$tool_input" | jq -r '.tool_input.currentPhase // 0')

  if [ -z "$agent_name" ]; then
    log "check-phase-order.allowed | no agentName in input, allowing"
    printf '{"allowed":true}\n'
    exit 0
  fi

  if [ "$current_phase" -eq 0 ]; then
    log "check-phase-order.allowed | no currentPhase in input, allowing"
    printf '{"allowed":true}\n'
    exit 0
  fi

  checkPhaseOrder "$agent_name" "$current_phase"
}

main "$@"
