#!/bin/bash
# build-checklist.sh — Build initial markdown checklist from parsed issues
# Input: JSON from parse-issues.sh
# Output: Path to created checklist file
#
# Usage:
#   bash build-checklist.sh '{"issues": [...]}'
#   checklistPath=$(bash build-checklist.sh "$issueData")

set -euo pipefail

ISSUE_DATA="${1:-.}"

# Get the work directory
WORK_DIR="${DARK_FACTORY_WORK_DIR:-.}"

CHECKLIST_PATH="$WORK_DIR/improve-checklist.md"

# Create checklist file with header
cat > "$CHECKLIST_PATH" << 'EOF'
# Improvement Checklist

This checklist tracks all violations to be fixed in the dark-factory improvement loop.
Each item will be marked [x] as it is fixed and processed.

EOF

# Parse the JSON and add each issue to the checklist
if command -v jq &> /dev/null; then
  # Use jq to iterate over issues
  ISSUE_COUNT=$(echo "$ISSUE_DATA" | jq '.issues | length')

  if [[ "$ISSUE_COUNT" -eq 0 ]]; then
    echo "Error: No valid issues parsed" >&2
    echo ""
    exit 1
  fi

  # Add each issue to the checklist
  echo "$ISSUE_DATA" | jq -r '.issues[] |
    if .type == "github" then
      "- [ ] #\(.number) — \(.title) (\(.body | split("\n")[0]))"
    else
      "- [ ] \"\(.description)\" — (freeform violation)"
    end' >> "$CHECKLIST_PATH"

else
  # Fallback if jq is not available (shouldn't happen in practice)
  echo "Error: jq is required but not found" >&2
  exit 1
fi

# Verify checklist was created and has content
if [[ ! -f "$CHECKLIST_PATH" ]] || [[ ! -s "$CHECKLIST_PATH" ]]; then
  echo "Error: Failed to create checklist" >&2
  exit 1
fi

# Output the path to the checklist
echo "$CHECKLIST_PATH"
