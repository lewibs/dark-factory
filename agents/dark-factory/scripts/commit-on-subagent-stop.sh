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
  *)
    echo "agent_type not recognized: $agent_type" >&2
    exit 0
    ;;
esac

work_dir="${DARK_FACTORY_WORK_DIR:-}"
if [ -z "$work_dir" ]; then
  echo "DARK_FACTORY_WORK_DIR not set, skipping commit" >&2
  exit 0
fi

if git -C "$work_dir" diff --cached --quiet 2>/dev/null; then
  echo "no staged changes in $work_dir, skipping commit" >&2
  exit 0
fi

git -C "$work_dir" add --all 2>/dev/null || {
  echo "git add failed in $work_dir" >&2
  exit 0
}

if ! git -C "$work_dir" commit -m "$commit_msg" 2>/dev/null; then
  echo "git commit failed in $work_dir" >&2
  exit 0
fi

commit_hash=$(git -C "$work_dir" rev-parse HEAD 2>/dev/null || echo "unknown")
echo "committed $commit_msg ($commit_hash)" >&2

exit 0
