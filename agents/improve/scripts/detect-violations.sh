#!/bin/bash
# detect-violations.sh — Scan agent behavior logs for pipeline instruction violations
# Input: Work directory from a manufacture run
# Output: JSON array of detected violations
#
# Scans the complete agent execution chain (feature-agent → execution-agent →
# implementation-agent → pr-agent → code-review-agent, etc.) for statements
# indicating pipeline instruction violations.
#
# Usage:
#   bash detect-violations.sh /path/to/manufacture/workdir
#
# Output format (JSON):
# [
#   { "category": "missing-coauthored-by", "agentName": "feature-agent",
#     "quote": "...", "description": "..." },
#   ...
# ]

set -euo pipefail

WORK_DIR="${1:-.}"

# Check that work directory exists
if [[ ! -d "$WORK_DIR" ]]; then
  echo "[]"  # Return empty array if workdir doesn't exist
  exit 0
fi

# Temporary file for collecting violations
VIOLATIONS_FILE=$(mktemp)
trap "rm -f $VIOLATIONS_FILE" EXIT

# Initialize violations JSON array
echo "[]" > "$VIOLATIONS_FILE"

# ── Helper function to add a violation ──
add_violation() {
  local category="$1"
  local agent_name="$2"
  local quote="$3"
  local description="$4"

  VIOLATION="{
    \"category\": \"$category\",
    \"agentName\": \"$agent_name\",
    \"quote\": $(echo "$quote" | jq -Rs .),
    \"description\": $(echo "$description" | jq -Rs .)
  }"

  VIOLATIONS=$(cat "$VIOLATIONS_FILE")
  echo "$VIOLATIONS" | jq ".+= [$VIOLATION]" > "$VIOLATIONS_FILE"
}

# ── Scan for violation patterns ──

# Look for agent log files or transcripts in the work directory
# Typically stored in logs/, transcripts/, or agent-output/ directories
LOG_DIRS=("$WORK_DIR/logs" "$WORK_DIR/transcripts" "$WORK_DIR/agent-output" "$WORK_DIR")

for LOG_DIR in "${LOG_DIRS[@]}"; do
  [[ ! -d "$LOG_DIR" ]] && continue

  # ── Detection Pattern 1: Agent explicitly states it skipped a required step ──
  # Look for patterns like: "I will skip", "skipping", "bypassing"
  while IFS= read -r line; do
    if grep -iq "skip.*hook\|bypass.*hook\|skip.*required\|skip.*test\|skip.*doc" <<< "$line"; then
      # Extract agent name from filename or context
      AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" <<< "$line" | head -1 || echo "unknown-agent")

      add_violation \
        "skipped-required-step" \
        "$AGENT_NAME" \
        "$line" \
        "Agent explicitly stated it is skipping a required step"
    fi
  done < <(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) -exec grep -h . {} \; 2>/dev/null | head -500)

  # ── Detection Pattern 2: Missing Co-Authored-By footer ──
  # Look for patterns like: "add Co-Authored-By", "forgot Co-Authored-By", "missing footer"
  while IFS= read -r line; do
    if grep -iq "co-author\|coauthor" <<< "$line"; then
      AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" <<< "$line" | head -1 || echo "unknown-agent")

      add_violation \
        "missing-coauthored-by" \
        "$AGENT_NAME" \
        "$line" \
        "Co-Authored-By footer may be missing or incorrect"
    fi
  done < <(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) -exec grep -h . {} \; 2>/dev/null | head -500)

  # ── Detection Pattern 3: Commits in wrong order ──
  # Look for patterns like: "committed before review", "commit before test"
  while IFS= read -r line; do
    if grep -iq "commit.*before\|before.*commit\|wrong.*order" <<< "$line"; then
      AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" <<< "$line" | head -1 || echo "unknown-agent")

      add_violation \
        "commit-sequence-violation" \
        "$AGENT_NAME" \
        "$line" \
        "Tool calls or commits may have been made in the wrong order"
    fi
  done < <(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) -exec grep -h . {} \; 2>/dev/null | head -500)

  # ── Detection Pattern 4: AskUserQuestion depth violation ──
  # Look for patterns like: "AskUserQuestion at depth", "called AskUserQuestion directly"
  while IFS= read -r line; do
    if grep -iq "askuserquestion.*depth\|ask.*user.*question.*wrong" <<< "$line"; then
      AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" <<< "$line" | head -1 || echo "unknown-agent")

      add_violation \
        "askuserquestion-depth-violation" \
        "$AGENT_NAME" \
        "$line" \
        "AskUserQuestion called at incorrect depth in agent chain"
    fi
  done < <(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) -exec grep -h . {} \; 2>/dev/null | head -500)

  # ── Detection Pattern 5: Sub-agent delegation failure ──
  # Look for patterns like: "failed to audit", "child agent violated", "delegation failure"
  while IFS= read -r line; do
    if grep -iq "delegation.*fail\|failed.*audit\|child.*agent.*violated" <<< "$line"; then
      AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" <<< "$line" | head -1 || echo "unknown-agent")

      add_violation \
        "sub-agent-delegation-failure" \
        "$AGENT_NAME" \
        "$line" \
        "Parent agent failed to properly audit or enforce pipeline compliance in delegated sub-agent"
    fi
  done < <(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) -exec grep -h . {} \; 2>/dev/null | head -500)

  # ── Detection Pattern 6: Missing test coverage ──
  # Look for patterns like: "no tests", "skip test", "untested code"
  while IFS= read -r line; do
    if grep -iq "skip.*test\|no.*test\|untested\|missing.*test" <<< "$line"; then
      AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" <<< "$line" | head -1 || echo "unknown-agent")

      add_violation \
        "missing-test-coverage" \
        "$AGENT_NAME" \
        "$line" \
        "Code was created without corresponding test coverage"
    fi
  done < <(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) -exec grep -h . {} \; 2>/dev/null | head -500)

  # ── Detection Pattern 7: Incomplete documentation ──
  # Look for patterns like: "skip doc", "no documentation", "incomplete docs"
  while IFS= read -r line; do
    if grep -iq "skip.*doc\|no.*doc\|incomplete.*doc" <<< "$line"; then
      AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" <<< "$line" | head -1 || echo "unknown-agent")

      add_violation \
        "incomplete-documentation" \
        "$AGENT_NAME" \
        "$line" \
        "Documentation updates were skipped or incomplete"
    fi
  done < <(find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) -exec grep -h . {} \; 2>/dev/null | head -500)

done

# Check for brain.json which may contain metrics about the manufacture run
if [[ -f "$WORK_DIR/brain.json" ]]; then
  # Look for indication of hard-stop or failure in brain.json
  if grep -iq "hard-stop\|hardstop\|execution.*failed" "$WORK_DIR/brain.json"; then
    add_violation \
      "execution-failure" \
      "execution-agent" \
      "brain.json indicates hard-stop" \
      "Execution phase encountered an error that should have been surfaced as a pipeline violation"
  fi
fi

# Output all detected violations
cat "$VIOLATIONS_FILE"
