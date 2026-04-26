# Tests

## Overview

The `tests/` directory contains regression tests that guard against known failure modes discovered during development. Tests are written in Python and run with `pytest`.

## Test Files

### test_push_notification_declared.py

**File:** `tests/test_push_notification_declared.py`

**Purpose:** Ensures that every agent which calls `PushNotification` in its body also declares `PushNotification` in its YAML front-matter `tools:` field. The Claude Code runtime silently skips tool calls for tools not listed in `tools:`, so a missing declaration causes notifications to be dropped without any error.

**What it tests:** Each of the 8 agents known to use `PushNotification`:

- `agents/featurework/agents/feature-agent.md`
- `agents/featurework/planning/agents/planning-agent.md`
- `agents/featurework/execution/agents/execution-agent.md`
- `agents/fix-flow/agents/fix-flow-orchestrator.md`
- `agents/fix-flow/agents/ralph-fix-and-push.md`
- `agents/dark-factory/agents/dark-factory-agent.md`
- `agents/documentation/agents/detect-drift-agent.md`
- `agents/documentation/agents/update-documentation-agent.md`

**For each agent the test:**

1. Asserts the agent file exists.
2. Parses the YAML front-matter block (`---` delimiters) and extracts the `tools:` value.
3. Asserts the agent body (after front-matter) references `PushNotification` — to catch stale entries in the test list.
4. Asserts `PushNotification` appears in the parsed tools list.

**Parametrized with:** `@pytest.mark.parametrize` — one test case per agent path.

## Running Tests

```bash
pytest tests/
```

## Background

These tests were added after the bug documented in `docs/bugs/2026-04-25-push-notification-missing-from-tools.md`, where `PushNotification` calls were silently dropped because agents did not declare the tool in their front-matter.
