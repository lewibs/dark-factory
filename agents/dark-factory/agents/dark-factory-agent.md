---
name: dark-factory-agent-batch-enabled
user-invocable: false
description: Updated dark-factory-agent with Batch API support. Orchestrates manufacture flow with optional batching of non-interactive agents (skill-update-agent, update-documentation-agent) for 50% token cost savings.
tools: Read, Bash, Agent, PushNotification, AskUserQuestion, Skill
model: haiku
---

# dark-factory-agent (Batch API Enhanced)

**Version**: 1.2.36+ (with Batch API support)

This is the updated dark-factory-agent with integrated Anthropic Batch API support for non-interactive agents.

## Key Changes

### Batch Processing Support

Steps 8 (update-documentation-agent) and 9 (skill-update-agent) can now use Batch API:

1. **Backward Compatible**: Default behavior (`DARK_FACTORY_BATCH_MODE=sync`) is identical to previous versions
2. **Cost Savings**: ~50% reduction in token costs for these non-interactive operations
3. **Configurable**: Three modes available:
   - `sync` (default): Queue jobs, block until completion, proceed with PR
   - `async`: Queue jobs, proceed with PR immediately, results are eventual-consistent
   - `poll`: Try quick poll (10s), continue regardless, results cached for later

### Implementation Details

#### New Scripts

Three new Python scripts manage batching:

- **batch-request-builder.py**: Converts agent invocation arguments into Batch API job requests
- **batch-poll-manager.py**: Polls Batch API for job completion and retrieves results
- **batch-queue-manager.py**: Orchestrates job submission and status tracking

#### Configuration

Add to `.claude/settings.json` or environment:

```json
{
  "DARK_FACTORY_BATCH_MODE": "sync"  // or "async" or "poll"
}
```

#### Batch Job Metadata

Batch job information stored in work directory:

```
work_dir/
  batch-jobs/
    update-documentation-agent-request.json    (Batch API request payload)
    update-documentation-agent-result.json     (Poll results)
    skill-update-agent-request.json
    skill-update-agent-result.json
```

## Orchestration Flow (Updated Steps 8-9)

### Step 8: Update Documentation (Batch-Enabled)

```pseudocode
batchMode = get_config("DARK_FACTORY_BATCH_MODE", "sync")

if batchMode == "sync" (DEFAULT):
  # Queue batch job, block until completion
  docJobId = queue_batch_job("update-documentation-agent", {planFilePath, workDir: WORK_DIR})
  docResult = poll_batch_job(docJobId, timeout=120)
  
  # Merge results into brain.json
  invoke brain-state-manager({
    operation: "patch",
    workDir: WORK_DIR,
    fieldsObject: {
      docsWritten: docResult.result.docsWritten || null,
      phases: { "docs-complete": true }
    }
  })

elif batchMode == "async":
  # Queue and continue
  docJobId = queue_batch_job("update-documentation-agent", {planFilePath, workDir: WORK_DIR})
  invoke brain-state-manager({
    operation: "patch",
    workDir: WORK_DIR,
    fieldsObject: {
      batchJobIds: [docJobId],
      phases: { "docs-complete": false }
    }
  })

elif batchMode == "poll":
  # Try quick poll (10s)
  docJobId = queue_batch_job("update-documentation-agent", {planFilePath, workDir: WORK_DIR})
  docResult = poll_batch_job(docJobId, timeout=10)
  
  if docResult.status == "completed":
    invoke brain-state-manager({
      operation: "patch",
      workDir: WORK_DIR,
      fieldsObject: {
        docsWritten: docResult.result.docsWritten || null,
        phases: { "docs-complete": true }
      }
    })
  else:
    # Don't block, update later
    invoke brain-state-manager({
      operation: "patch",
      workDir: WORK_DIR,
      fieldsObject: {
        batchJobIds: [docJobId],
        phases: { "docs-complete": false }
      }
    })
```

### Step 9: Skill Update (Batch-Enabled, Non-Fatal)

```pseudocode
try:
  if batchMode == "sync":
    skillJobId = queue_batch_job("skill-update-agent", {planFilePath, workDir, taskDescription})
    skillResult = poll_batch_job(skillJobId, timeout=120)
    
    invoke brain-state-manager({
      operation: "patch",
      workDir: WORK_DIR,
      fieldsObject: {
        skillsWritten: skillResult.result.skillsWritten || null,
        phases: { "skills-complete": true }
      }
    })
  
  elif batchMode == "async":
    skillJobId = queue_batch_job("skill-update-agent", {planFilePath, workDir, taskDescription})
    invoke brain-state-manager({
      operation: "patch",
      workDir: WORK_DIR,
      fieldsObject: {
        batchJobIds: [skillJobId],
        phases: { "skills-complete": false }
      }
    })
  
  elif batchMode == "poll":
    skillJobId = queue_batch_job("skill-update-agent", {planFilePath, workDir, taskDescription})
    skillResult = poll_batch_job(skillJobId, timeout=10)
    
    if skillResult.status == "completed":
      invoke brain-state-manager({
        operation: "patch",
        workDir: WORK_DIR,
        fieldsObject: {
          skillsWritten: skillResult.result.skillsWritten || null,
          phases: { "skills-complete": true }
        }
      })
    else:
      invoke brain-state-manager({
        operation: "patch",
        workDir: WORK_DIR,
        fieldsObject: {
          batchJobIds: [skillJobId],
          phases: { "skills-complete": false }
        }
      })

catch error:
  warn "skill-update-agent batch job failed. Continuing to PR."
```

## Helper Functions

### queue_batch_job(agentName, agentArgs) → jobId

Submits a batch job request to Anthropic Batch API.

```bash
python3 batch-queue-manager.py \
  --command submit \
  --agent "$agentName" \
  --agent-args "$agentArgs" \
  --work-dir "$WORK_DIR"
```

### poll_batch_job(jobId, timeout) → {status, result, error}

Polls Batch API for job completion with timeout.

```bash
python3 batch-queue-manager.py \
  --command poll \
  --job-id "$jobId" \
  --work-dir "$WORK_DIR" \
  --timeout "$timeout"
```

## Benefits & Tradeoffs

### Batch Mode: sync (Recommended for Production)

**Benefits**:
- 100% backward compatible (no behavior change from user's perspective)
- 50% cost savings on token consumption
- No eventual consistency issues
- Results guaranteed before PR opens

**Tradeoffs**:
- Slightly slower per manufacture (waiting for batch processing)
- Requires Batch API quota/account setup

### Batch Mode: async (Recommended for Development)

**Benefits**:
- Faster PR opening (batch jobs run in parallel with PR CI)
- Cost savings with eventual consistency
- Non-blocking for manufacture flow

**Tradeoffs**:
- Docs and skills may not be fully written when PR opens
- Requires post-PR audit/verification step

### Batch Mode: poll (Experimental)

**Benefits**:
- Non-blocking, best-effort results
- Manufacture completes quickly
- Backward compatible if batch job fails

**Tradeoffs**:
- Uncertain completion time
- May miss fast batch completions (10s timeout is aggressive)
- Results cached for later retrieval

## Testing

### Unit Tests

```bash
# Test batch request builder
python3 -m pytest tests/test_batch_request_builder.py

# Test batch polling
python3 -m pytest tests/test_batch_poll_manager.py

# Test queue manager
python3 -m pytest tests/test_batch_queue_manager.py
```

### Integration Tests

```bash
# Test manufacture flow with batch mode
DARK_FACTORY_BATCH_MODE=sync python3 -m pytest tests/test_manufacture_batch_flow.py

# Verify docs/skills written correctly
python3 -m pytest tests/test_batch_results_merged.py
```

## Rollout Plan

1. **Phase 1** (Current): Merge batch scripts, keep default `DARK_FACTORY_BATCH_MODE=sync`
2. **Phase 2** (Next): Monitor batch job success rates, adjust timeouts/retry logic
3. **Phase 3** (Future): Enable `async` mode by default for faster manufacture flows
4. **Phase 4** (Future): Deprecate synchronous agent invocation in non-batch mode

## Configuration Reference

```json
{
  "DARK_FACTORY_BATCH_MODE": "sync",       // sync | async | poll
  "DARK_FACTORY_BATCH_TIMEOUT_SYNC": 120,  // seconds
  "DARK_FACTORY_BATCH_TIMEOUT_QUICK": 10,  // for poll/async modes
  "DARK_FACTORY_BATCH_POLL_INTERVAL": 5,   // seconds between polls
  "DARK_FACTORY_BATCH_ENABLED": true       // global toggle
}
```

## Rules

- **Backward Compatibility**: Default sync mode is 100% compatible with pre-batch behavior
- **Graceful Degradation**: If Batch API is unavailable, fall back to synchronous invocation
- **Non-Fatal**: skill-update-agent failures must not block PR opening (existing behavior preserved)
- **Idempotency**: Batch jobs can be safely retried; system handles duplicate submissions
- Never invoke the built-in `Explore` subagent_type directly. Always route codebase research through `investigation-agent` — it checks existing docs first (cheap) before scanning the codebase.

