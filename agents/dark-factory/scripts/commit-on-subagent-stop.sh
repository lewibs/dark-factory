#!/usr/bin/env bash
# commit-on-subagent-stop.sh
# Hook script called by the SubagentStop hook when skeleton-agent, testing-agent,
# or implementation-agent finishes execution. Commits staged changes in the
# feature worktree with an agent-specific commit message.
#
# Flow: hook-fired

agent_type=$(head -n1)

case "$agent_type" in
  skeleton-agent)
    commit_msg="skeleton"
    ;;
  testing-agent)
    commit_msg="tests"
    ;;
  implementation-agent)
    commit_msg="implementation"
    ;;
  sub-planning-agent)
    commit_msg="plan"
    ;;
  detect-drift-agent)
    commit_msg="docs: fix drift"
    ;;
  update-documentation-agent)
    commit_msg="docs: update documentation"
    ;;
  skill-update-agent)
    commit_msg="chore: update skills"
    ;;
  setup-wizard)
    commit_msg="chore: add setup scripts"
    ;;
  reproduce-test-agent)
    bug_slug=$(cat /tmp/dark-factory-bug-slug 2>/dev/null || echo "reproduction")
    commit_msg="test: $bug_slug (red)"
    ;;
  debugger-fix-agent)
    bug_slug=$(cat /tmp/dark-factory-bug-slug 2>/dev/null || echo "bug")
    commit_msg="fix: $bug_slug"
    ;;
  debugger-agent)
    bug_slug=$(cat /tmp/dark-factory-bug-slug 2>/dev/null || echo "debug")
    commit_msg="fix: $bug_slug"
    ;;
  repair-agent)
    commit_msg="fix: repair"
    ;;
  *)
    echo "agent_type not recognized: $agent_type" >&2
    exit 0
    ;;
esac

work_dir="${DARK_FACTORY_WORK_DIR:-$(cat /tmp/dark-factory-work-dir 2>/dev/null)}"
if [ -z "$work_dir" ]; then
  echo "DARK_FACTORY_WORK_DIR not set, skipping commit" >&2
  exit 0
fi

if git -C "$work_dir" diff --cached --quiet 2>/dev/null; then
  echo "no staged changes in $work_dir, skipping commit" >&2
  exit 0
fi

if ! git -C "$work_dir" commit -m "$commit_msg" 2>/dev/null; then
  echo "git commit failed in $work_dir" >&2
  exit 0
fi

commit_hash=$(git -C "$work_dir" rev-parse HEAD 2>/dev/null || echo "unknown")
echo "committed $commit_msg ($commit_hash)" >&2

exit 0
