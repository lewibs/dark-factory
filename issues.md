# Code Review Issues: Debug Flow Fix

## Critical Issues (Must Fix Before Merge)

### Issue #1: debugger-agent.md Missing git Allowed-Tool
- **Severity:** BLOCKING
- **Location:** agents/debugger/agents/debugger-agent.md (line 8)
- **Problem:** Step 7 requires `git add` and `git commit` but `allowed-tools: Bash(bash *), Bash(pytest *)...` does not include `Bash(git *)`
- **Impact:** Agent will fail at runtime when attempting to commit fix
- **Current:** `allowed-tools: Bash(bash *), Bash(pytest *), Bash(python *), Bash(npm test *), Bash(grep -r *), Bash(find *)`
- **Required Fix:** Add `Bash(git *)` to allowed-tools
- **Status:** RESOLVED

### Issue #2: debug-flow-agent.md Missing git Allowed-Tool
- **Severity:** BLOCKING
- **Location:** agents/fix-flow/agents/debug-flow-agent.md (line 8)
- **Problem:** Step 7 requires `git add --all && git commit` but `allowed-tools: Bash(bash trigger.sh), Bash(bash wait-for-completion.sh), Bash(bash fetch-logs.sh)` is too restrictive
- **Impact:** Agent will fail at runtime when attempting to commit changes
- **Current:** `allowed-tools: Bash(bash trigger.sh), Bash(bash wait-for-completion.sh), Bash(bash fetch-logs.sh)`
- **Required Fix:** Add `Bash(git *)` to allowed-tools
- **Status:** RESOLVED

### Issue #3: debug-flow-agent.md pr-agent Invocation Incomplete
- **Severity:** BLOCKING
- **Location:** agents/fix-flow/agents/debug-flow-agent.md (Step 8, line 28)
- **Problem:** Instructions say "Invoke `pr-agent` to open a PR with the fix" but do not specify what inputs to pass. pr-agent requires either planFilePath or taskDescription as input.
- **Impact:** Agent cannot invoke pr-agent correctly; missing required inputs
- **Current:** Line 28 just says "Invoke `pr-agent` to open a PR with the fix"
- **Required Fix:** Specify inputs, e.g., "Invoke `pr-agent` with bugFilePath and git diff of the fix" or similar
- **Status:** RESOLVED

### Issue #4: fix-flow-orchestrator.md Missing Agent Tool
- **Severity:** BLOCKING
- **Location:** agents/fix-flow/agents/fix-flow-orchestrator.md (line 5)
- **Problem:** YAML `tools:` list is `Read, Bash, PushNotification, AskUserQuestion` but Step 1 requires invoking investigation-agent and Phase 3 requires invoking ralph-fix-and-push. Agent tool is required to invoke other agents.
- **Impact:** Orchestrator will fail when attempting to spawn sub-agents
- **Current:** `tools: Read, Bash, PushNotification, AskUserQuestion`
- **Required Fix:** Add `Agent` to tools list
- **Status:** RESOLVED

### Issue #5: debug-flow-agent.md YAML Description Outdated
- **Severity:** HIGH
- **Location:** agents/fix-flow/agents/debug-flow-agent.md (line 4)
- **Problem:** YAML description says "does not create PRs" but Step 8 now invokes pr-agent to create PR. Description is contradictory to implementation.
- **Impact:** Confusing for maintainers; signals incomplete refactoring of agent responsibilities
- **Current:** "...Returns a bug explanation and code fix — does not create PRs or deploy."
- **Required Fix:** Update to reflect new behavior: "...Returns a PR URL with the fix implemented and submitted."
- **Status:** RESOLVED

## Medium Priority Issues (Should Fix)

### Issue #6: Infinite Loop Risk in debug-flow-agent
- **Severity:** MEDIUM
- **Location:** agents/fix-flow/agents/debug-flow-agent.md (Step 6, lines 22-25)
- **Problem:** Instruction says "report to debugger-agent for another iteration" but has no maximum retry limit or loop logic. Could loop indefinitely.
- **Impact:** Agents could become stuck if debugger-agent repeatedly fails to produce working fix
- **Status:** RESOLVED

### Issue #7: Verification Mechanism Unspecified
- **Severity:** MEDIUM
- **Location:** agents/fix-flow/agents/debug-flow-agent.md (Step 6, lines 22-23)
- **Problem:** Step 6 says "Confirm the code changes exist in the working tree" but provides no explicit verification method
- **Impact:** Unclear how agent determines if fix is actually present; could proceed with incomplete fixes
- **Recommendation:** Specify method, e.g., "Run `git diff --exit-code` to verify changes exist and `npm test` to verify they work"
- **Status:** RESOLVED

### Issue #8: Missing Error Handling in Orchestrator Phases
- **Severity:** MEDIUM
- **Location:** agents/fix-flow/agents/fix-flow-orchestrator.md (Phase 1 and Phase 2)
- **Problem:** Phase 1 (lines 24-29) invokes investigation-agent and Phase 2 (lines 31-38) invokes setup-wizard with no error handling. If either fails, orchestrator proceeds anyway.
- **Impact:** Phase 3 could attempt to fix without required setup (system diagram or scripts)
- **Status:** RESOLVED

### Issue #9: Commit Responsibility Split Unclear
- **Severity:** MEDIUM
- **Location:** agents/debugger/agents/debugger-agent.md (Step 7) vs agents/fix-flow/agents/debug-flow-agent.md (Step 7)
- **Problem:** Both agents mention committing changes. debugger-agent says "Commit the fix" and debug-flow-agent says "Commit all changes". Unclear who is responsible.
- **Impact:** Could result in attempted double-commits or missed commits
- **Recommendation:** Clarify that debugger-agent applies code changes (modifies files) but does NOT commit. Only debug-flow-agent commits via `git add && git commit`
- **Status:** RESOLVED

## Summary

**Status:** Cannot merge in current state due to 5 blocking issues.

**Blocking Issues:** 5 (Issues #1-5)
- debugger-agent missing git allowed-tool
- debug-flow-agent missing git allowed-tool  
- debug-flow-agent pr-agent invocation incomplete
- fix-flow-orchestrator missing Agent tool
- debug-flow-agent YAML description outdated

**Non-Blocking Issues:** 4 (Issues #6-9)
- Infinite loop risk (no retry limit)
- Verification mechanism unspecified
- Error handling missing in orchestrator phases
- Commit responsibility unclear

## Positive Findings

✓ **Strategic Intent:** The instruction changes successfully eliminate the diagnosis-only pattern that was blocking fix completions

✓ **Production Debugging:** New requirements for live log checking, database queries, and pipeline tracing are appropriate and necessary for real-world bug fixes

✓ **Completion Enforcement:** PR URL requirement forces actual implementation, not just diagnosis. This is a critical safeguard.

✓ **Verification:** Test suite verification before committing is a good safeguard against shipping broken fixes

✓ **Documentation:** Bug audit log linking in PR description creates good documentation trail

✓ **Orchestrator Completeness:** Orchestrator explicitly rejects partial completion (diagnosis without fix), which is the right design choice

✓ **Investigation Integration:** Use of investigation-agent for system understanding is correctly designed

✓ **Investigation-Agent Pattern:** Proper routing through investigation-agent instead of built-in Explore, per project guidelines
