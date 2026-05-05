#!/usr/bin/env bash
# commit-investigation-docs.sh
# SubagentStop hook for the investigation command.
# Called when investigation-orchestrator finishes. Commits the verified
# docs/docs/<system>.md file to the repo.
#
# Flow: hook-fired

agent_type=$(head -n1)

if [ "$agent_type" != "investigation-orchestrator" ]; then
  exit 0
fi

work_dir="${DARK_FACTORY_WORK_DIR:-}"
if [ -z "$work_dir" ]; then
  work_dir=$(cat /tmp/dark-factory-work-dir 2>/dev/null || true)
fi
if [ -z "$work_dir" ]; then
  echo "DARK_FACTORY_WORK_DIR not set, skipping commit" >&2
  exit 0
fi

# Stage any new or updated docs/docs/ files
git -C "$work_dir" add docs/docs/ 2>/dev/null || {
  echo "git add docs/docs/ failed in $work_dir" >&2
  exit 0
}

if git -C "$work_dir" diff --cached --quiet 2>/dev/null; then
  echo "no staged changes in $work_dir/docs/docs/, skipping commit" >&2
  exit 0
fi

if ! git -C "$work_dir" commit -m "docs: add verified system documentation" 2>/dev/null; then
  echo "git commit failed in $work_dir" >&2
  exit 0
fi

commit_hash=$(git -C "$work_dir" rev-parse HEAD 2>/dev/null || echo "unknown")
echo "committed verified docs ($commit_hash)" >&2

exit 0
