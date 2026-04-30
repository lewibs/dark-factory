#!/bin/bash
# update-checklist.sh — Update the improvement checklist (mark items checked, add new issues)
# Supports three operations: --mark-checked, --add-issue, --mark-failed
#
# Usage:
#   bash update-checklist.sh --mark-checked /path/to/checklist.md "#42"
#   bash update-checklist.sh --mark-failed /path/to/checklist.md "#42"
#   bash update-checklist.sh --add-issue /path/to/checklist.md "#456"

set -euo pipefail

OPERATION="${1:-.}"
CHECKLIST_PATH="${2:-.}"
ITEM_SPEC="${3:-.}"

# Validate inputs
if [[ ! -f "$CHECKLIST_PATH" ]]; then
  echo "Error: Checklist file not found: $CHECKLIST_PATH" >&2
  exit 1
fi

case "$OPERATION" in
  --mark-checked)
    # Mark item as checked: change "- [ ]" to "- [x]" for matching line
    # ITEM_SPEC is the identifier (e.g., "#42" or "violation description")

    # Escape special regex characters in ITEM_SPEC
    ESCAPED_ITEM=$(printf '%s\n' "$ITEM_SPEC" | sed 's/[[\.*^$/]/\\&/g')

    # Use sed to find and replace the first unchecked item containing ITEM_SPEC
    sed -i "s/^- \[ \] \($ESCAPED_ITEM\|.*$ESCAPED_ITEM.*\)/- [x] \1/" "$CHECKLIST_PATH"

    if [[ $? -eq 0 ]]; then
      echo "Marked item as checked: $ITEM_SPEC"
    else
      echo "Warning: Could not mark item as checked" >&2
    fi
    ;;

  --mark-failed)
    # Mark item as failed: change "- [ ]" to "- [x] FAILED" for matching line
    ESCAPED_ITEM=$(printf '%s\n' "$ITEM_SPEC" | sed 's/[[\.*^$/]/\\&/g')

    sed -i "s/^- \[ \] \($ESCAPED_ITEM\|.*$ESCAPED_ITEM.*\)/- [x] FAILED: \1/" "$CHECKLIST_PATH"

    if [[ $? -eq 0 ]]; then
      echo "Marked item as failed: $ITEM_SPEC"
    else
      echo "Warning: Could not mark item as failed" >&2
    fi
    ;;

  --add-issue)
    # Add a new issue to the checklist
    # ITEM_SPEC is the issue number (e.g., "#456") or description
    # Append as unchecked item at the end of the list

    if [[ "$ITEM_SPEC" =~ ^#[0-9]+$ ]]; then
      # GitHub issue number — fetch title
      ISSUE_NUMBER="${ITEM_SPEC#\#}"

      if command -v gh &> /dev/null; then
        ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --json number,title --jq '.' 2>/dev/null || echo '{}')

        if [[ "$ISSUE_JSON" != "{}" ]]; then
          TITLE=$(echo "$ISSUE_JSON" | jq -r '.title // "N/A"')
          NEW_ITEM="- [ ] $ISSUE_NUMBER — $TITLE (auto-detected violation)"
        else
          NEW_ITEM="- [ ] $ISSUE_NUMBER — (violation found, title unavailable)"
        fi
      else
        NEW_ITEM="- [ ] $ISSUE_NUMBER — (violation found)"
      fi
    else
      # Freeform description
      NEW_ITEM="- [ ] \"$ITEM_SPEC\" — (auto-detected violation)"
    fi

    # Append to checklist
    echo "$NEW_ITEM" >> "$CHECKLIST_PATH"

    echo "Added new issue to checklist: $ITEM_SPEC"
    ;;

  *)
    echo "Usage: update-checklist.sh --mark-checked|--mark-failed|--add-issue <checklist-path> <item-spec>" >&2
    exit 1
    ;;
esac

exit 0
