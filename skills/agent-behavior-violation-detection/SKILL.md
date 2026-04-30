---
name: agent-behavior-violation-detection
description: "Use this skill when building a post-manufacture auditor that scans agent execution logs and transcripts for pipeline instruction violations expressed in the agents' own words or tool call patterns."
user-invocable: false
---
## When to use

After a manufacture run, when you need to detect whether any agent in the execution chain violated pipeline instructions. This is distinct from checking git diffs — you are auditing what agents *said* and *decided*, not just what they produced.

Use when:
- Building an improvement loop that feeds violations back into the checklist
- Adding a CI-level audit step after manufacture
- Diagnosing why a manufacture run produced an incorrect result

## Steps

1. Define the log search paths — agent logs may appear in multiple locations within the manufacture work directory:
   ```bash
   LOG_DIRS=("$WORK_DIR/logs" "$WORK_DIR/transcripts" "$WORK_DIR/agent-output" "$WORK_DIR")
   ```

2. For each log directory that exists, scan `.log`, `.txt`, and `.md` files for violation patterns using `grep -iq` (case-insensitive, quiet):
   ```bash
   find "$LOG_DIR" -type f \( -name "*.log" -o -name "*.txt" -o -name "*.md" \) \
     -exec grep -h . {} \; 2>/dev/null | head -500
   ```
   The `head -500` prevents reading enormous transcripts; adjust if needed.

3. Use `grep -iq` pattern matching for each violation category separately — do not combine all patterns into one pass, as you need per-category metadata:
   ```bash
   # Category: explicit step-skip
   if grep -iq "i will skip\|i'm skipping\|bypassing.*hook\|skip.*required.*step" <<< "$line"; then ...

   # Category: missing Co-Authored-By
   if grep -iq "forgot.*co-author\|missing.*co-author\|add.*co-author.*footer" <<< "$line"; then ...

   # Category: commit sequence violation
   if grep -iq "commit.*before\|wrong.*order" <<< "$line"; then ...

   # Category: AskUserQuestion depth
   if grep -iq "askuserquestion.*depth\|ask.*user.*question.*wrong" <<< "$line"; then ...

   # Category: sub-agent delegation failure
   if grep -iq "delegation.*fail\|failed.*audit\|child.*agent.*violated" <<< "$line"; then ...

   # Category: missing tests
   if grep -iq "skip.*test\|no.*test\|untested\|missing.*test" <<< "$line"; then ...
   ```

4. Extract the agent name from each matching line using a pattern match against known agent names, with fallback:
   ```bash
   AGENT_NAME=$(grep -o "feature-agent\|execution-agent\|implementation-agent\|pr-agent\|code-review-agent" \
     <<< "$line" | head -1 || echo "unknown-agent")
   ```

5. Build a JSON violation entry using `jq -Rs .` to safely encode multi-line quotes:
   ```bash
   add_violation() {
     local category="$1" agent_name="$2" quote="$3" description="$4"
     VIOLATION="{
       \"category\": \"$category\",
       \"agentName\": \"$agent_name\",
       \"quote\": $(echo "$quote" | jq -Rs .),
       \"description\": $(echo "$description" | jq -Rs .)
     }"
     VIOLATIONS=$(cat "$VIOLATIONS_FILE")
     echo "$VIOLATIONS" | jq ".+= [$VIOLATION]" > "$VIOLATIONS_FILE"
   }
   ```

6. Also check `brain.json` in the work directory for hard-stop signals — these indicate execution-level failures that surface as violations:
   ```bash
   if [[ -f "$WORK_DIR/brain.json" ]]; then
     if grep -iq "hard-stop\|hardstop\|execution.*failed" "$WORK_DIR/brain.json"; then
       add_violation "execution-failure" "execution-agent" \
         "brain.json indicates hard-stop" \
         "Execution phase encountered an error"
     fi
   fi
   ```

7. Deduplicate violations before returning using `jq unique_by`:
   ```bash
   cat "$VIOLATIONS_FILE" | jq 'unique_by({category, agentName, quote})'
   ```

8. Return an empty array `[]` (not an error) when the work directory does not exist — callers must handle missing log dirs gracefully.

## Notes

- The detection approach is heuristic, not exhaustive. It finds violations where agents *expressed* them in language. Silent violations (agent just didn't do the step without saying so) are not detectable by log scanning alone — those require checking the git diff or artifact state separately.
- The `grep -iq` patterns must be conservative: prefer false negatives over false positives. A spurious violation creates unnecessary GitHub issues; a missed violation is just not caught this cycle.
- Keep each detection pattern in its own `while IFS= read -r line; do ... done` loop — this makes it easy to add, remove, or tune categories independently.
- The `jq -Rs .` idiom safely encodes arbitrary text (including newlines, backslashes, and quotes) as a JSON string. Never use `echo "\"$variable\""` for user-derived content.
- Violation categories to cover at minimum: `skipped-required-step`, `missing-coauthored-by`, `commit-sequence-violation`, `askuserquestion-depth-violation`, `sub-agent-delegation-failure`, `missing-test-coverage`, `incomplete-documentation`, `execution-failure`.
