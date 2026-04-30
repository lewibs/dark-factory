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
    # Use atomic write: write to temp file, then move

    # Escape special regex characters in ITEM_SPEC
    ESCAPED_ITEM=$(printf '%s\n' "$ITEM_SPEC" | sed 's/[[\.*^$/]/\\&/g')

    # Create temporary file in the same directory to ensure atomic move
    TMP_CHECKLIST="${CHECKLIST_PATH}.tmp.$$"

    # Use sed to find and replace the first unchecked item containing ITEM_SPEC
    if sed "s/^- \[ \] \($ESCAPED_ITEM\|.*$ESCAPED_ITEM.*\)/- [x] \1/" "$CHECKLIST_PATH" > "$TMP_CHECKLIST"; then
      mv "$TMP_CHECKLIST" "$CHECKLIST_PATH"
      echo "Marked item as checked: $ITEM_SPEC"
    else
      rm -f "$TMP_CHECKLIST"
      echo "Warning: Could not mark item as checked" >&2
    fi
    ;;

  --mark-failed)
    # Mark item as failed: change "- [ ]" to "- [x] FAILED" for matching line
    # Use atomic write

    ESCAPED_ITEM=$(printf '%s\n' "$ITEM_SPEC" | sed 's/[[\.*^$/]/\\&/g')
    TMP_CHECKLIST="${CHECKLIST_PATH}.tmp.$$"

    if sed "s/^- \[ \] \($ESCAPED_ITEM\|.*$ESCAPED_ITEM.*\)/- [x] FAILED: \1/" "$CHECKLIST_PATH" > "$TMP_CHECKLIST"; then
      mv "$TMP_CHECKLIST" "$CHECKLIST_PATH"
      echo "Marked item as failed: $ITEM_SPEC"
    else
      rm -f "$TMP_CHECKLIST"
      echo "Warning: Could not mark item as failed" >&2
    fi
    ;;

  --add-issue)
    # Add a new issue to the checklist
    # ITEM_SPEC is the issue number (e.g., "#456") or description
    # Append as unchecked item at the end of the list
    # Use atomic write for safety

    if [[ "$ITEM_SPEC" =~ ^#[0-9]+$ ]]; then
      # GitHub issue number — fetch title
      ISSUE_NUMBER="${ITEM_SPEC#\#}"

      if command -v gh &> /dev/null; then
        ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --json number,title 2>/dev/null || echo '')

        if [[ -n "$ISSUE_JSON" ]]; then
          TITLE=$(echo "$ISSUE_JSON" | jq -r '.title // "N/A"')
          NEW_ITEM="- [ ] #$ISSUE_NUMBER — $TITLE (auto-detected violation)"
        else
          NEW_ITEM="- [ ] #$ISSUE_NUMBER — (violation found, title unavailable)"
        fi
      else
        NEW_ITEM="- [ ] #$ISSUE_NUMBER — (violation found)"
      fi
    else
      # Freeform description
      # Check if already quoted; if so, use as-is, otherwise add quotes
      if [[ "$ITEM_SPEC" =~ ^\".*\"$ ]]; then
        NEW_ITEM="- [ ] $ITEM_SPEC — (auto-detected violation)"
      else
        NEW_ITEM="- [ ] \"$ITEM_SPEC\" — (auto-detected violation)"
      fi
    fi

    # Append to checklist atomically
    TMP_CHECKLIST="${CHECKLIST_PATH}.tmp.$$"
    cp "$CHECKLIST_PATH" "$TMP_CHECKLIST"
    echo "$NEW_ITEM" >> "$TMP_CHECKLIST"
    mv "$TMP_CHECKLIST" "$CHECKLIST_PATH"

    echo "Added new issue to checklist: $ITEM_SPEC"
    ;;

  *)
    echo "Usage: update-checklist.sh --mark-checked|--mark-failed|--add-issue <checklist-path> <item-spec>" >&2
    exit 1
    ;;
esac

exit 0
