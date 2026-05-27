# Manufacture Flow with Batch API Processing

**Related**: batch-api-processing.md

## Overview

The dark-factory manufacture flow orchestrates work end-to-end: prep → execution → review → docs → skills → PR → cleanup.

As of v1.2.36, Steps 8 (update-documentation-agent) and 9 (skill-update-agent) optionally use Batch API for non-interactive processing.

## Modified Steps

### Step 8: Update Documentation (Batch-Enabled)

**Purpose**: Update project documentation to reflect implemented changes.

**Before (v1.2.35)**:
```pseudocode
invoke update-documentation-agent({ planFilePath })
  # Synchronous: blocks until agent completes
  # Cost: ~3,000 tokens (full price)
```

**After (v1.2.36+)**:
```pseudocode
batchMode = get_config("DARK_FACTORY_BATCH_MODE", "sync")

if batchMode == "sync":
  jobId = queue_batch_job("update-documentation-agent", {planFilePath})
  result = poll_batch_job(jobId, timeout=120)
  invoke brain-state-manager({
    operation: "patch",
    fieldsObject: {
      docsWritten: result.docsWritten,
      phases: { "docs-complete": true }
    }
  })
  # Same result as before, 50% cheaper

elif batchMode == "async":
  jobId = queue_batch_job("update-documentation-agent", {planFilePath})
  # Don't wait; continue to Step 9
  # Job finishes asynchronously while PR opens

elif batchMode == "poll":
  jobId = queue_batch_job("update-documentation-agent", {planFilePath})
  result = poll_batch_job(jobId, timeout=10)  # Short timeout
  if result.status == "completed":
    merge_results(result.docsWritten)
  # Continue to Step 9 regardless
```

**Behavior Changes**:
- Sync mode: No visible change (still blocks, still merges results, 50% cheaper)
- Async mode: Proceeds immediately, docs written async
- Poll mode: Tries quick poll, proceeds with or without results

### Step 9: Skill Update (Batch-Enabled, Non-Fatal)

**Purpose**: Extract reusable patterns from completed work.

**Before (v1.2.35)**:
```pseudocode
try:
  invoke skill-update-agent({ planFilePath, workDir, taskSummary })
catch:
  warn "skill-update-agent failed. Continuing to PR."
  # Non-fatal: failure doesn't block PR
```

**After (v1.2.36+)**:
```pseudocode
try:
  batchMode = get_config("DARK_FACTORY_BATCH_MODE", "sync")
  
  if batchMode == "sync":
    jobId = queue_batch_job("skill-update-agent", {...})
    result = poll_batch_job(jobId, timeout=120)
    merge_results(result.skillsWritten)
  
  elif batchMode == "async":
    jobId = queue_batch_job("skill-update-agent", {...})
    # Don't wait; continue to Step 10
  
  elif batchMode == "poll":
    jobId = queue_batch_job("skill-update-agent", {...})
    result = poll_batch_job(jobId, timeout=10)
    if result.status == "completed":
      merge_results(result.skillsWritten)
    # Continue to Step 10 regardless

catch:
  warn "skill-update-agent batch job failed. Continuing to PR."
  # Still non-fatal in batch mode
```

**Behavior Changes**:
- Sync mode: No visible change (still blocks, still optional, 50% cheaper)
- Async mode: Proceeds immediately, skills written async
- Poll mode: Tries quick poll, continues with or without results
- Failure handling: Same as before (non-fatal, logs warning)

## Updated Manufacture Flow Diagram

```
┌─────────────────────────────────────────┐
│ Step 1-7: Existing (No Changes)         │
│ - Classify task                         │
│ - Prep work dir                         │
│ - Create brain.json                     │
│ - Route to worker (feature/fix/repair)  │
│ - Branch drift guard                    │
│ - Code review                           │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────┐
        │ Step 8: Docs │ (Batch-Enabled)
        └──────┬───────┘
               │
        ┌──────▼──────────┐
        │ Check BATCH_MODE │
        └──────┬───────────┘
               │
        ┌──────┴─────────┬──────────┐
        │                │          │
     [sync]          [async]    [poll]
        │                │          │
    Queue +          Queue    Queue +
    Poll           Don't       Quick
   (120s)          Wait        Poll
    Wait            (10s)
  Merge             Continue
 Continue           Async
        │                │          │
        └────────┬───────┴──────────┘
                 │
        ┌────────▼──────────┐
        │ Step 9: Skills    │ (Batch-Enabled, Non-Fatal)
        └────────┬──────────┘
                 │
        ┌────────▼───────────┐
        │ Check BATCH_MODE   │
        └────────┬───────────┘
                 │
        ┌────────┴─────────┬──────────┐
        │                  │          │
     [sync]            [async]    [poll]
        │                  │          │
    Queue +            Queue    Queue +
    Poll             Don't      Quick
   (120s)            Wait       Poll
    Wait             (10s)
  Merge              Continue
 Continue            Async
        │                  │          │
        └──────────┬───────┴──────────┘
                   │
        ┌──────────▼─────────┐
        │ Step 10: Open PR   │
        │ (Always blocks)    │
        └──────────┬─────────┘
                   │
        ┌──────────▼─────────────┐
        │ Step 11-12: Cleanup    │
        │ (Existing, No Changes) │
        └────────────────────────┘
```

## Configuration Reference

### Default Configuration

```json
{
  "DARK_FACTORY_BATCH_MODE": "sync",             // Recommended default
  "DARK_FACTORY_BATCH_ENABLED": true,
  "DARK_FACTORY_BATCH_TIMEOUT_SYNC": 120,
  "DARK_FACTORY_BATCH_TIMEOUT_QUICK": 10,
  "DARK_FACTORY_BATCH_POLL_INTERVAL": 5
}
```

### Setting Configuration

**Option 1: Environment Variable**
```bash
export DARK_FACTORY_BATCH_MODE=sync
/dark-factory:manufacture [task]
```

**Option 2: .claude/settings.json**
```json
{
  "DARK_FACTORY_BATCH_MODE": "sync"
}
```

**Option 3: Per-Task Override**
```bash
DARK_FACTORY_BATCH_MODE=async /dark-factory:manufacture [task]
```

## Impact on Manufacture Duration

### Sync Mode (Default)

```
Total manufacture time = Existing time + Polling overhead
Polling overhead: ~2-3 seconds per job (batch API latency)
Overall impact: +2-3 seconds per manufacture (~1-2% slower)
Cost impact: -50% on docs/skills processing
```

### Async Mode

```
Total manufacture time = Existing time (skips polling)
Polling overhead: 0 seconds (fire-and-forget)
Overall impact: -5-10 seconds per manufacture (faster!)
Cost impact: -50% on docs/skills processing
Tradeoff: Eventual consistency (docs/skills written after PR opens)
```

### Poll Mode

```
Total manufacture time = Existing time + Quick poll (10s max)
Polling overhead: ~10 seconds worst case (times out)
Overall impact: Variable (-10 to +10 seconds)
Cost impact: -50% on docs/skills processing
Tradeoff: Best-effort (may not get results)
```

## Results Tracking in brain.json

After Steps 8-9 complete, brain.json updated with:

```json
{
  "docsWritten": [
    "/path/to/work_dir/docs/docs/new-flow.md",
    "/path/to/work_dir/docs/docs/existing-flow.md"
  ],
  "skillsWritten": [
    {
      "path": "skills/handle-git-merge/SKILL.md",
      "action": "created"
    },
    {
      "path": "skills/existing-pattern/SKILL.md",
      "action": "updated"
    }
  ],
  "batchJobIds": [
    "custom_id_docs_abc123",
    "custom_id_skills_def456"
  ],
  "phases": {
    "docs-complete": true,    // true if sync/async mode succeeded or poll got results
    "skills-complete": true   // true if sync/async mode succeeded or poll got results
  }
}
```

## Error Handling

### Batch Job Submission Fails

**Scenario**: batch-request-builder fails

**Handling**:
- Log error
- Fall back to synchronous invocation (if mode="sync")
- Log warning and continue without results (if mode="async" or "poll")
- Non-fatal for skill-update-agent (existing behavior)

### Polling Timeout

**Scenario**: Batch job doesn't complete within timeout

**Handling**:
- Sync mode: Log error, retry with longer timeout, or fail manufacture
- Async mode: Job ID recorded; continue to PR (results may arrive later)
- Poll mode: No results available; continue to PR (graceful degradation)

### Result Parsing Fails

**Scenario**: Batch API returns unexpected response format

**Handling**:
- Try/except JSON parsing
- Log error but don't block
- Continue without merging results
- Non-fatal (docs/skills missing is acceptable)

## Migration from Non-Batch to Batch

**No migration needed**. The batch system is:

1. **Opt-in**: Default is sync mode, which is 100% backward compatible
2. **Transparent**: Users see no behavior change in sync mode
3. **Safe**: Graceful fallback if Anthropic SDK missing
4. **Non-breaking**: Existing non-batch manufacture flows continue to work

## Testing Recommendations

### Pre-Release Testing

1. **Sync Mode**: Run full manufacture flow 10 times, verify results identical to non-batch
2. **Async Mode**: Run 5 times, manually verify batch jobs completed after PR opened
3. **Poll Mode**: Run 5 times, verify manufacture completes quickly
4. **Failure Cases**: Disable Anthropic SDK, verify fallback to non-batch

### Post-Release Monitoring

1. **Success Rate**: Monitor batch job completion rates in production
2. **Latency**: Measure polling overhead vs. expected ~2-3 seconds
3. **Cost**: Verify token savings match 50% reduction assumption
4. **Reliability**: Alert on batch API failures

## Future Enhancements

### Phase 2: Async Mode as Default
- Monitor sync mode success rates for 1 month
- Switch default to `DARK_FACTORY_BATCH_MODE=async`
- Build post-PR batch result audit tools
- Document async mode best practices

### Phase 3: Monitoring Dashboard
- Add real-time batch job status display
- Build cost tracking per manufacture
- Alert on batch API quota usage

### Phase 4: Advanced Batching
- Batch code review agent (currently synchronous)
- Batch PR agent (currently synchronous)
- Combine all eligible agents into single batch submission

