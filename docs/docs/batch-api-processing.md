# Batch API Processing for Non-Interactive Agents

**Status**: Implemented in v1.2.36+

**Purpose**: Enable asynchronous batch processing of non-interactive dark-factory agents (skill-update-agent and update-documentation-agent) via Anthropic's Batch API for 50% token cost reduction.

## Overview

The dark-factory manufacture flow invokes two heavy-lifting agents at the end:

1. **Step 8**: update-documentation-agent (updates project docs based on implementation)
2. **Step 9**: skill-update-agent (extracts reusable patterns from completed work)

Both agents are **non-interactive** — they don't need real-time responses from the user. The Anthropic Batch API is designed for exactly this use case: async job processing at 50% token cost.

## Architecture

### Three Processing Modes

The batch system supports three modes, controlled by `DARK_FACTORY_BATCH_MODE` config:

#### 1. Sync (Default, Recommended)

Queue both agents as batch jobs and wait for completion before opening PR.

```
manufacture flow
  ↓
Step 8: Queue update-documentation-agent → Batch API
Step 9: Queue skill-update-agent → Batch API
  ↓
Poll for completion (timeout: 120s each)
  ↓
Merge results into brain.json
  ↓
Step 10: Open PR (with docs/skills guaranteed written)
```

**Behavior**: Identical to pre-batch behavior, but 50% cheaper.

**Benefits**:
- 100% backward compatible
- Results guaranteed before PR opens
- Cost savings without tradeoffs

**Tradeoffs**:
- Slightly slower per manufacture (polling overhead)
- Requires Batch API quota setup

#### 2. Async (Experimental)

Queue batch jobs and immediately proceed to PR opening.

```
manufacture flow
  ↓
Step 8: Queue update-documentation-agent → Batch API (fire-and-forget)
Step 9: Queue skill-update-agent → Batch API (fire-and-forget)
  ↓
Record job IDs in brain.json
  ↓
Step 10: Open PR (batch jobs still processing)
  ↓
Batch results available later for audit
```

**Behavior**: PR opens immediately, batch jobs finish asynchronously.

**Benefits**:
- Faster PR opening (skip polling)
- Cost savings
- Non-blocking manufacture flow

**Tradeoffs**:
- Docs/skills eventual-consistent (may not be in PR when opened)
- Requires post-PR audit to verify completion

#### 3. Poll (Experimental)

Try a quick 10-second poll for each job, proceed with or without results.

```
manufacture flow
  ↓
Step 8: Queue update-documentation-agent → Batch API
Step 9: Queue skill-update-agent → Batch API
  ↓
Quick poll (timeout: 10s each)
  ↓
Merge available results
  ↓
Step 10: Open PR (with partial or no batch results)
```

**Behavior**: Non-blocking, best-effort attempt to get results.

**Benefits**:
- Very fast if batch jobs complete quickly
- Non-blocking
- Graceful degradation if jobs timeout

**Tradeoffs**:
- Uncertain completion
- May miss slow batch completions
- Results cached for later retrieval

### Component Architecture

```
dark-factory-agent (orchestrator)
  ↓ (Step 8-9)
batch-queue-manager.py (CLI orchestrator)
  ├─ submit command → batch-request-builder.py
  │   ↓
  │   Anthropic Batch API (job submission)
  │
  └─ poll command → batch-poll-manager.py
      ↓
      Anthropic Batch API (status check + results)
```

## Implementation Details

### Scripts

Three new Python scripts manage batch operations:

#### batch-request-builder.py

Converts agent invocation arguments into Batch API job requests.

```bash
python3 batch-request-builder.py \
  --agent update-documentation-agent \
  --agent-args '{"planFilePath": "/path/to/plan.md"}' \
  --work-dir /path/to/work_dir \
  --output /path/to/request.json
```

Generates Batch API request payload with:
- Agent-specific system prompt
- User message with serialized arguments
- Model: claude-3-5-sonnet-20241022
- Max tokens: 8000

#### batch-poll-manager.py

Polls Batch API for job completion with configurable timeout.

```bash
python3 batch-poll-manager.py \
  --job-id batch_abc123... \
  --timeout 120 \
  --output /path/to/results.json
```

Returns structured result:
```json
{
  "jobId": "batch_abc123...",
  "status": "completed|failed|timeout|error",
  "result": [...],
  "error": null
}
```

#### batch-queue-manager.py

Orchestrates job submission and polling lifecycle.

```bash
# Submit a batch job
python3 batch-queue-manager.py \
  --command submit \
  --agent update-documentation-agent \
  --agent-args '{"planFilePath": "/path/to/plan.md"}' \
  --work-dir /path/to/work_dir

# Poll for results
python3 batch-queue-manager.py \
  --command poll \
  --job-id batch_abc123... \
  --work-dir /path/to/work_dir \
  --timeout 120
```

### Configuration

Control batching behavior via environment or `.claude/settings.json`:

```json
{
  "DARK_FACTORY_BATCH_MODE": "sync",             // sync | async | poll
  "DARK_FACTORY_BATCH_ENABLED": true,            // global toggle
  "DARK_FACTORY_BATCH_TIMEOUT_SYNC": 120,        // sync mode timeout (seconds)
  "DARK_FACTORY_BATCH_TIMEOUT_QUICK": 10,        // async/poll timeout (seconds)
  "DARK_FACTORY_BATCH_POLL_INTERVAL": 5          // interval between polls
}
```

### Integration with dark-factory-agent

Steps 8-9 of the manufacture flow are updated:

**Step 8: Update Documentation**

```pseudocode
if BATCH_MODE == "sync":
  jobId = queue_batch_job("update-documentation-agent", {planFilePath})
  result = poll_batch_job(jobId, timeout=120)
  merge_results_to_brain_json(result.docsWritten)
  
elif BATCH_MODE == "async":
  jobId = queue_batch_job("update-documentation-agent", {planFilePath})
  record_job_id_in_brain_json(jobId)
  # Don't wait; continue to Step 9

elif BATCH_MODE == "poll":
  jobId = queue_batch_job("update-documentation-agent", {planFilePath})
  result = poll_batch_job(jobId, timeout=10)
  if result.status == "completed":
    merge_results_to_brain_json(result.docsWritten)
  # Continue regardless
```

**Step 9: Skill Update** (identical pattern, non-fatal)

### Brain State Management

Batch job metadata stored in brain.json:

```json
{
  "batchJobIds": ["custom_id_abc...", "custom_id_def..."],
  "docsWritten": ["/path/to/written.md"],
  "skillsWritten": [{"path": "skills/pattern.md", "action": "created"}],
  "phases": {
    "docs-complete": true,    // sync mode: true after polling
    "skills-complete": true   // async mode: may be false
  }
}
```

### Job Metadata Storage

Batch job metadata persisted in work directory:

```
work_dir/batch-jobs/
  update-documentation-agent-request.json   (Batch API request payload)
  update-documentation-agent-result.json    (Poll results)
  skill-update-agent-request.json
  skill-update-agent-result.json
```

## Cost Analysis

### Token Usage Comparison

**Without Batch API** (per manufacture):
- update-documentation-agent: ~3,000 tokens
- skill-update-agent: ~2,500 tokens
- Total: ~5,500 tokens

**With Batch API** (50% discount):
- update-documentation-agent: ~1,500 tokens
- skill-update-agent: ~1,250 tokens
- Total: ~2,750 tokens

**Savings**: 50% reduction

### Annual Savings (1000 manufactures/month)

```
Before: $0.0165/manufacture × 12,000/year = $198/year
After:  $0.00825/manufacture × 12,000/year = $99/year
Savings: $99/year (50%)
```

## Testing

### Unit Tests

```bash
# Test request building
python3 -m pytest tests/test_batch_request_builder.py -v

# Test polling logic
python3 -m pytest tests/test_batch_poll_manager.py -v

# Test orchestration
python3 -m pytest tests/test_batch_queue_manager.py -v
```

### Integration Tests

```bash
# Test full manufacture flow with batching
DARK_FACTORY_BATCH_MODE=sync python3 -m pytest tests/test_manufacture_batch_flow.py -v

# Verify results merged correctly
python3 -m pytest tests/test_batch_results_merged.py -v
```

## Troubleshooting

### Batch Job Submission Fails

**Error**: "batch-request-builder failed"

**Causes**:
- Anthropic SDK not installed
- Invalid agent name
- Invalid JSON arguments

**Solution**:
```bash
pip install anthropic
python3 batch-request-builder.py --help
echo '{"planFilePath": "/tmp/plan.md"}' | jq .
```

### Polling Timeout

**Error**: "Job {jobId} did not complete within {timeout}s"

**Causes**:
- Batch API taking longer than timeout
- Job actually failed on Batch API side

**Solution**:
```bash
# Increase timeout
DARK_FACTORY_BATCH_TIMEOUT_SYNC=300 /dark-factory:manufacture [task]

# Check Batch API dashboard
# https://console.anthropic.com/account/usage
```

### Results Not Merged

**Error**: brain.json missing docsWritten or skillsWritten after completion

**Causes**:
- Polling returned non-completed status
- Result JSON parsing failed

**Solution**:
```bash
# Check batch results file
cat /path/to/work_dir/batch-jobs/*-result.json | jq .

# Manually patch brain.json if needed
python3 brain-state-manager.py patch \
  --work-dir /path/to/work_dir \
  --field docsWritten \
  --value '["/path/to/doc.md"]'
```

## Backward Compatibility

**Default behavior (DARK_FACTORY_BATCH_MODE=sync) is 100% backward compatible**:

- Same cost for tasks already using Batch API (now at 50% discount)
- Same results for tasks not using Batch API yet
- No behavior changes visible to users
- Graceful degradation if Anthropic SDK missing

## Rollout Plan

### Phase 1: Implementation & Validation (Current)
- [x] Implement batch request builder
- [x] Implement batch polling manager
- [x] Implement queue orchestrator
- [x] Write comprehensive tests
- [x] Document implementation

### Phase 2: Production Testing (Next)
- [ ] Merge to main
- [ ] Enable sync mode by default
- [ ] Monitor batch job success rates
- [ ] Adjust timeouts based on real-world data

### Phase 3: Async Mode Support (Future)
- [ ] Enable async mode for development
- [ ] Build post-PR result audit tools

### Phase 4: Deprecation (Future)
- [ ] Deprecate synchronous agent invocation
- [ ] Make Batch API the default

## References

- [Anthropic Batch API Docs](https://docs.anthropic.com/en/docs/build/batch)
- [Implementation Plan](/docs/plans/2026-05-06-batch-api-agents.md)
- [Guide & Examples](./BATCH_API_README.md)

