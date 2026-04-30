#!/bin/bash
# create-issue.sh — Create a GitHub issue for a detected violation
# Input: JSON violation object
# Output: GitHub issue number
#
# Usage:
#   bash create-issue.sh '{"category": "missing-coauthored-by", "agentName": "feature-agent", "quote": "...", "description": "..."}'
#   issueNumber=$(bash create-issue.sh "$violation")

set -euo pipefail

VIOLATION="${1:-.}"

# Parse the violation JSON
if command -v jq &> /dev/null; then
  CATEGORY=$(echo "$VIOLATION" | jq -r '.category // "unknown"')
  AGENT_NAME=$(echo "$VIOLATION" | jq -r '.agentName // "unknown-agent"')
  QUOTE=$(echo "$VIOLATION" | jq -r '.quote // ""')
  DESCRIPTION=$(echo "$VIOLATION" | jq -r '.description // ""')
else
  echo "Error: jq is required but not found" >&2
  exit 1
fi

# Construct issue title and body
TITLE="Pipeline violation: $CATEGORY in $AGENT_NAME"

BODY="## Violation Type
\`$CATEGORY\`

## Violating Agent
\`$AGENT_NAME\`

## Description
$DESCRIPTION

## Agent Quote
\`\`\`
$QUOTE
\`\`\`

## Context
This violation was automatically detected by the dark-factory:improve orchestrator while scanning agent behavior logs for pipeline instruction violations.

---

**Category codes:**
- \`missing-coauthored-by\` — Co-Authored-By footer missing or incorrect
- \`skipped-required-step\` — Agent skipped a step marked as required
- \`commit-sequence-violation\` — Commits made in wrong order
- \`askuserquestion-depth-violation\` — AskUserQuestion called at wrong depth
- \`sub-agent-delegation-failure\` — Parent agent failed to audit child agent
- \`missing-test-coverage\` — Code created without tests
- \`incomplete-documentation\` — Documentation updates skipped
- \`execution-failure\` — Execution phase encountered unhandled error
- \`other\` — Other pipeline instruction violation
"

# Create GitHub issue with the violation label
# gh issue create outputs the issue URL on success
ISSUE_OUTPUT=$(gh issue create \
  --title "$TITLE" \
  --body "$BODY" \
  --label "pipeline-violation" \
  2>&1)

if [[ $? -eq 0 ]]; then
  # Extract the issue number from the output
  # Output format: "https://github.com/owner/repo/issues/NNNN"
  ISSUE_NUMBER=$(echo "$ISSUE_OUTPUT" | grep -o '[0-9]\+$' | head -1)

  if [[ -n "$ISSUE_NUMBER" ]]; then
    echo "$ISSUE_NUMBER"
    exit 0
  fi
fi

# If creation failed or we couldn't extract the number, return error
# Fallback to fetching last issue is unreliable and not recommended
echo "Error: Failed to create GitHub issue" >&2
exit 1
