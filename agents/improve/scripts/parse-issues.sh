#!/bin/bash
# parse-issues.sh — Parse a comma-separated list of GitHub issue numbers and/or freeform descriptions
# Output: JSON array of parsed issues
#
# Usage:
#   bash parse-issues.sh "#42, #123, \"violation description\""
#   bash parse-issues.sh "#42"
#   bash parse-issues.sh "\"missing Co-Authored-By in repair-agent\""
#
# Output format (JSON):
# {
#   "issues": [
#     { "type": "github", "number": 42, "title": "...", "body": "..." },
#     { "type": "freeform", "description": "..." }
#   ]
# }

set -euo pipefail

ISSUE_LIST="${1:-.}"

# Initialize JSON output
OUTPUT='{"issues": []}'

# Temporary files for parsing
TMP_ISSUES=$(mktemp)
trap "rm -f $TMP_ISSUES" EXIT

# Parse the comma-separated list
# Split on commas, but respect quoted strings
# We'll use a simple approach: split on comma, then check each item

IFS=',' read -ra ITEMS <<< "$ISSUE_LIST"

for item in "${ITEMS[@]}"; do
  # Trim whitespace
  item=$(echo "$item" | xargs)

  # Skip empty items
  [[ -z "$item" ]] && continue

  # Check if it's a GitHub issue number (#NN) or a quoted freeform description
  if [[ "$item" =~ ^#([0-9]+)$ ]]; then
    # GitHub issue number with # prefix
    NUMBER="${BASH_REMATCH[1]}"

    # Fetch issue details using gh CLI
    ISSUE_JSON=$(gh issue view "$NUMBER" --json number,title,body 2>/dev/null || echo '')

    if [[ -n "$ISSUE_JSON" ]]; then
      # Successfully fetched GitHub issue
      TITLE=$(echo "$ISSUE_JSON" | jq -r '.title // "N/A"')
      BODY=$(echo "$ISSUE_JSON" | jq -r '.body // ""' | head -c 500)  # First 500 chars of body

      # Add to JSON, using proper jq escaping
      ISSUE_ENTRY=$(jq -n --arg type "github" --argjson number "$NUMBER" --arg title "$TITLE" --arg body "$BODY" \
        '{type: $type, number: $number, title: $title, body: $body}')
      OUTPUT=$(echo "$OUTPUT" | jq ".issues += [$ISSUE_ENTRY]")
    else
      # GitHub issue not found, skip it
      echo "Warning: GitHub issue #$NUMBER not found, skipping" >&2
    fi

  elif [[ "$item" =~ ^\"(.*)\"$ ]]; then
    # Freeform description (quoted)
    DESCRIPTION="${BASH_REMATCH[1]}"

    ISSUE_ENTRY=$(jq -n --arg type "freeform" --arg description "$DESCRIPTION" \
      '{type: $type, description: $description}')
    OUTPUT=$(echo "$OUTPUT" | jq ".issues += [$ISSUE_ENTRY]")

  else
    # Unquoted item — could be a GitHub number without # or a naked description
    # Try to interpret as GitHub number first
    if [[ "$item" =~ ^[0-9]+$ ]]; then
      # Numeric only — treat as GitHub issue
      NUMBER="$item"
      ISSUE_JSON=$(gh issue view "$NUMBER" --json number,title,body 2>/dev/null || echo '')

      if [[ -n "$ISSUE_JSON" ]]; then
        TITLE=$(echo "$ISSUE_JSON" | jq -r '.title // "N/A"')
        BODY=$(echo "$ISSUE_JSON" | jq -r '.body // ""' | head -c 500)

        ISSUE_ENTRY=$(jq -n --arg type "github" --argjson number "$NUMBER" --arg title "$TITLE" --arg body "$BODY" \
          '{type: $type, number: $number, title: $title, body: $body}')
        OUTPUT=$(echo "$OUTPUT" | jq ".issues += [$ISSUE_ENTRY]")
      else
        echo "Warning: GitHub issue #$NUMBER not found, skipping" >&2
      fi
    else
      # Treat as freeform description
      ISSUE_ENTRY=$(jq -n --arg type "freeform" --arg description "$item" \
        '{type: $type, description: $description}')
      OUTPUT=$(echo "$OUTPUT" | jq ".issues += [$ISSUE_ENTRY]")
    fi
  fi
done

# Output the parsed issues as JSON
echo "$OUTPUT"
