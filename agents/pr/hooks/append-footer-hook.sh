#!/bin/bash

# Hook: append-footer-hook
# Purpose: Append "Made with dark-factory" footer to PR body at end-of-agent
# This hook runs after pr-agent completes to dynamically add the footer to PR descriptions
# Yama will invoke this script when pr-agent finishes (PostToolUse hook)
# IMPORTANT: PostToolUse hooks may be invoked multiple times during agent execution.
# The idempotency check ensures footer is only appended once per PR body.

set -e

# Function: append_footer_to_pr_body
# Input: PR body file path
# Output: Modified PR body with footer appended (with idempotency guard)
append_footer_to_pr_body() {
    local pr_body_file="$1"

    if [[ ! -f "$pr_body_file" ]]; then
        echo "Error: PR body file not found at $pr_body_file" >&2
        return 1
    fi

    # Idempotency guard: check if footer is already present
    # This prevents duplicate footers if hook is invoked multiple times
    if grep -qF "Generated with [dark factory]" "$pr_body_file"; then
        echo "Footer already present in PR body, skipping append" >&2
        return 0
    fi

    # Append the footer separator and footer text to the PR body
    # The footer was previously hardcoded in the template; now it's generated dynamically
    {
        cat "$pr_body_file"
        echo ""
        echo "---"
        echo "🤖 Generated with [dark factory](https://github.com/lewibs/dark-factory)"
    } > "$pr_body_file.tmp"

    mv "$pr_body_file.tmp" "$pr_body_file"

    return 0
}

# Main hook execution
# When invoked by Yama's end-of-agent hook mechanism:
# The PR body file can be passed via DARK_FACTORY_PR_BODY_FILE env var, command arg, or defaults to /tmp/pr-body.md
PR_BODY_FILE="${DARK_FACTORY_PR_BODY_FILE:-${1:-/tmp/pr-body.md}}"

if [[ -n "$PR_BODY_FILE" && -f "$PR_BODY_FILE" ]]; then
    append_footer_to_pr_body "$PR_BODY_FILE"
    exit 0
else
    # Hook may be invoked at other times; gracefully skip if no PR body file
    exit 0
fi
