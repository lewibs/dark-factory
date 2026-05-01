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

# ---------------------------------------------------------------------------
# checkPhaseOrder
# TODO (check-phase-order): Implement phase order validation.
#   - Read agentName and currentPhase from hook input.
#   - Look up agentName in the phase map.
#   - If agent is unknown, allow execution and exit 0.
#   - Read completedPhases from brain.json.
#   - If all phases 1..(currentPhase-1) are complete, allow execution.
#   - Otherwise, raise SubagentStop with a descriptive message listing the
#     incomplete phases.
# ---------------------------------------------------------------------------
checkPhaseOrder() {
  # TODO (check-phase-order): not implemented
  :
}

# ---------------------------------------------------------------------------
# markPhaseComplete
# TODO (mark-phase-complete): Implement phase completion marking.
#   - Accept agentName and phaseNumber.
#   - Acquire brain.json lock.
#   - Append phaseNumber to completedPhases array in brain.json.
#   - Release lock and return updated completedPhases list.
#   - On write error, return { updated: false, error: <message> }.
# ---------------------------------------------------------------------------
markPhaseComplete() {
  # TODO (mark-phase-complete): not implemented
  :
}

# ---------------------------------------------------------------------------
# main
# TODO (check-phase-order): Wire stdin → checkPhaseOrder → stdout/SubagentStop.
# ---------------------------------------------------------------------------
main() {
  # TODO (check-phase-order): not implemented
  cat  # pass through stdin unchanged (stub: no-op)
}

main "$@"
