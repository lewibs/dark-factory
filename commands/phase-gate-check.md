---
name: phase-gate-check
description: "Verify that phases run in declared order. Check if a phase can run or if prerequisites are blocked. Used for explicit phase enforcement."
user-invocable: false
---

# phase-gate-check

Enforce phase ordering and prerequisites before allowing a phase to run.

## Input

- `brainPath` — absolute path to brain.json (string)
- `phaseToCheck` — name of the phase to verify (string, e.g., "worker", "review", "docs")

## Output

### Phase can run
```json
{
  "success": true,
  "canRun": true,
  "phase": "worker",
  "message": "All prerequisites met"
}
```

### Phase blocked (prerequisite not complete)
```json
{
  "success": true,
  "canRun": false,
  "phase": "review",
  "prerequisite": "worker",
  "reason": "Worker phase is not yet complete",
  "blockingPhases": ["worker"]
}
```

### File not found
```json
{
  "success": false,
  "reason": "brain.json not found at <brainPath>"
}
```

## Phase Dependencies

The phase dependency order (from brain.json) is enforced as:

1. `prep` — must complete before any worker phase
2. `worker` — must complete before `review`
3. `review` — must complete before `docs`
4. `docs` — must complete before `skills`
5. `skills` — must complete before `pr`
6. `pr` — must complete before `cleanup`

(This ordering is defined in brain.json's `phases` object, but this command verifies the dependency chain.)

## Algorithm

1. Read brain.json from `brainPath`
2. For each phase with `*-complete: true`, mark as completed
3. Check if `phaseToCheck` has all its prerequisites complete
4. Return `canRun: true` if all prerequisites done, else `canRun: false` with blocking phases list

## Rules

- Phase names use the prefix only (e.g., "worker" not "worker-running" or "worker-complete")
- A phase can run if:
  - Its prerequisites (all earlier phases) are complete (`*-complete: true`)
  - OR it is the first phase (`prep`)
- Phases can only be checked after brain.json is created (by dark-factory-agent)
- This check is advisory; phases are ultimately ordered by the orchestrator
- If a phase has no blocking phases, `canRun: true` even if earlier phases are not yet started (for recovery scenarios)

## Integration

This command is used by orchestrators that need explicit phase enforcement:

```
gateResult = invoke phase-gate-check({
  brainPath: "$WORK_DIR/brain.json",
  phaseToCheck: "docs"
})

if gateResult.canRun == false:
  error "Cannot run docs phase: " + gateResult.reason
  stop

# gateResult.canRun == true
# proceed with phase
```

It can also be used in validation/testing to verify phase order:

```
# Verify that all required phases completed in order
for phase in ["prep", "worker", "review", "docs", "skills", "pr", "cleanup"]:
  gateResult = phase-gate-check(brainPath, phase)
  if gateResult.canRun == false:
    log "Phase " + phase + " cannot run: " + gateResult.reason
```
