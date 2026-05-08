#!/usr/bin/env bash
# append-pr-footer.sh
# SubagentStop hook: appends the "Made with dark-factory" footer to the open PR description.
# Triggered when the manufacturing agent stops after creating a PR.

set -e

# TODO: read PR number from brain.json or pointer file
# TODO: fetch current PR body via `gh pr view --json body`
# TODO: skip if footer already present (idempotency guard)
# TODO: append footer line to PR body
# TODO: update PR description via `gh pr edit --body`

exit 0
