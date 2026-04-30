---
name: improve
description: Continuously fixes pipeline instruction violations. Takes a list of issues (GitHub numbers or freeform descriptions), builds a checklist, iteratively invokes manufacture for each, detects new violations, creates GitHub issues for them, and reports final statistics.
tools: Bash, Skill, Read, Write, PushNotification, AskUserQuestion
model: haiku
allowed-tools: |
  Bash(bash ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/parse-issues.sh *),
  Bash(bash ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/build-checklist.sh *),
  Bash(bash ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/detect-violations.sh *),
  Bash(bash ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/create-issue.sh *),
  Bash(bash ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/update-checklist.sh *),
  Bash(grep *), Bash(find *), Bash(cat *), Bash(rm *), Bash(git *)
scripts: ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/parse-issues.sh, ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/build-checklist.sh, ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/detect-violations.sh, ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/create-issue.sh, ${CLAUDE_PLUGIN_ROOT}/agents/improve/scripts/update-checklist.sh
---

# dark-factory:improve

Continuously fixes pipeline instruction violations by iteratively identifying, fixing, and detecting new violations.

## Usage

```bash
/dark-factory:improve --issues "#42, #123, \"missing Co-Authored-By\""
```

Or via stdin:
```bash
echo "#42, \"violation description\"" | /dark-factory:improve
```

## What It Does

1. Parses a comma-separated list of GitHub issue numbers or freeform violation descriptions
2. Builds a markdown checklist tracking all violations to be fixed
3. For each unchecked item:
   - Invokes `/dark-factory:manufacture` to fix the violation
   - Scans the manufacture output for new pipeline instruction violations
   - Creates GitHub issues for any newly detected violations
   - Adds them to the checklist before marking the current item done
4. Reports final statistics (total fixed, total new violations, per-agent breakdown)

## Features

- **Flexible input**: accepts GitHub issue numbers (#42) or freeform descriptions ("missing Co-Authored-By in repair-agent")
- **Self-correcting**: automatically detects new violations introduced during fixes
- **Comprehensive auditing**: scans ALL agents in the execution chain (feature-agent, execution-agent, implementation-agent, pr-agent, code-review-agent, etc.)
- **Transparent tracking**: maintains a markdown checklist showing progress
- **Automated escalation**: creates GitHub issues for newly discovered violations

## Violation Detection

Detects violations across the full agent execution chain:
- Agent statements about skipping required steps
- Agent reasoning contradicting pipeline rules
- Sequence violations (steps done in wrong order)
- Sub-agent delegation failures
- Pipeline instruction propagation failures
- Agent reasoning contradictions
- Missing Co-Authored-By footers
- Skipped pre-commit hooks
- Non-atomic commits
- Missing test coverage
- Incomplete documentation

## Examples

Fix a single GitHub issue and any violations it introduces:
```bash
/dark-factory:improve --issues "#42"
```

Fix multiple GitHub issues plus custom violations:
```bash
/dark-factory:improve --issues "#42, #123, \"agent misuse in repair flow\""
```

Input via stdin:
```bash
gh issue list --label "pipeline-violation" --json number | jq -r '.[] | .number | "#\(.)"' | tr '\n' ',' | /dark-factory:improve
```

## Output

- `improve-checklist.md` — markdown checklist of all issues (original + newly discovered)
- Console report — final statistics with per-agent violation breakdown
- GitHub issues — created for each newly discovered violation
