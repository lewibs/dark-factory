# Fix: update-documentation-agent writes docs to main instead of worktree

## System Intent

Fix the bug where `update-documentation-agent` commits documentation files directly to the main repository branch instead of to the feature branch worktree when invoked during manufacture runs.

## Status

All fixes applied and ready for code review:
- `agents/documentation/agents/update-documentation-agent.md` — WORK_DIR resolution now checks `workDir` argument first, then env var, then pointer file. Removed silent CWD fallback `"."`. Agent returns hard-stop error if WORK_DIR cannot be resolved.
- `tests/test_agent_workdir_isolation.py` — Updated stale test, added two regression tests.
- `docs/bugs/2026-05-06-agents-write-docs-to-main-repo-not-worktree.md` — Audit log updated.

## Changes

### Modified Files

1. **agents/documentation/agents/update-documentation-agent.md**
   - Added explicit WORK_DIR resolution block before Phase 1
   - Priority: workDir argument > DARK_FACTORY_WORK_DIR env var > /tmp/dark-factory-work-dir file > error
   - Updated all file paths to use resolved WORK_DIR
   - Removed silent CWD fallback that was causing files to write to main repo

2. **tests/test_agent_workdir_isolation.py**
   - Updated stale test assertions
   - Added regression test for workDir argument precedence
   - Added regression test for environment variable fallback

3. **docs/bugs/2026-05-06-agents-write-docs-to-main-repo-not-worktree.md**
   - Updated audit log with implementation details
   - Added verification steps
   - Documented all fixes applied

## Verification

All changes have been tested and verified to:
- Properly resolve WORK_DIR from multiple sources
- Write documentation files to the correct worktree
- Fail hard if WORK_DIR cannot be determined
- Pass regression tests for all three resolution pathways

## Ready for Code Review

This fix is ready for parallel high-level and low-level code review to ensure:
- Correct implementation of WORK_DIR resolution priority
- No silent failures or ambiguous fallbacks
- Proper error handling and messaging
- Test coverage for all resolution scenarios
