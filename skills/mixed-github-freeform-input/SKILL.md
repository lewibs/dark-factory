---
name: mixed-github-freeform-input
description: "Use this skill when a command must accept a comma-separated list that mixes GitHub issue references (#42) with quoted freeform descriptions, normalize them to a single JSON structure, and handle both gracefully."
user-invocable: false
---
## When to use

When building a command that should accept issue references from multiple sources in a single argument:
- A list that mixes `#42`, `123` (bare number), and `"freeform text"` in one string
- The caller may pipe GitHub issue numbers from `gh issue list` or type descriptions directly
- The consuming agent needs a uniform JSON structure regardless of input form

## Steps

1. Accept input as a single comma-separated string (argument or stdin):
   ```bash
   ISSUE_LIST="${1:-}"
   ```

2. Split on commas with `IFS=','` — this handles the common case cleanly. Do NOT use `read -d` as it has portability issues with quoted commas inside items:
   ```bash
   IFS=',' read -ra ITEMS <<< "$ISSUE_LIST"
   ```

3. For each item, trim whitespace with `xargs` before classifying:
   ```bash
   item=$(echo "$item" | xargs)
   ```

4. Classify each item with ordered regex checks:
   ```bash
   if [[ "$item" =~ ^#([0-9]+)$ ]]; then
     # GitHub issue with # prefix
     NUMBER="${BASH_REMATCH[1]}"
   elif [[ "$item" =~ ^[0-9]+$ ]]; then
     # Bare numeric — treat as GitHub issue number
     NUMBER="$item"
   elif [[ "$item" =~ ^\"(.*)\"$ ]]; then
     # Quoted freeform description
     DESCRIPTION="${BASH_REMATCH[1]}"
   else
     # Unquoted freeform description (fallback)
     DESCRIPTION="$item"
   fi
   ```

5. For GitHub issue numbers, fetch metadata with `gh issue view` and handle failure gracefully:
   ```bash
   ISSUE_JSON=$(gh issue view "$NUMBER" --json number,title,body 2>/dev/null || echo '')
   if [[ -z "$ISSUE_JSON" ]]; then
     echo "Warning: GitHub issue #$NUMBER not found, skipping" >&2
     continue
   fi
   TITLE=$(echo "$ISSUE_JSON" | jq -r '.title // "N/A"')
   BODY=$(echo "$ISSUE_JSON" | jq -r '.body // ""' | head -c 500)
   ```

6. Build uniform JSON output using `jq -n` with `--arg` / `--argjson` to avoid shell-escaping bugs:
   ```bash
   # GitHub entry
   ENTRY=$(jq -n --arg type "github" --argjson number "$NUMBER" \
     --arg title "$TITLE" --arg body "$BODY" \
     '{type: $type, number: $number, title: $title, body: $body}')

   # Freeform entry
   ENTRY=$(jq -n --arg type "freeform" --arg description "$DESCRIPTION" \
     '{type: $type, description: $description}')

   OUTPUT=$(echo "$OUTPUT" | jq ".issues += [$ENTRY]")
   ```

7. Output the final JSON to stdout so callers can pipe it directly:
   ```bash
   echo "$OUTPUT"
   ```

## Notes

- Truncate issue body to ~500 chars with `head -c 500` — full bodies are rarely needed and can bloat JSON passed between scripts.
- Never use `echo "$var" | jq` for values that might contain newlines or special characters — always use `jq -n --arg` to safely inject shell variables into JSON.
- The `||` in `gh issue view ... 2>/dev/null || echo ''` is intentional: `gh` exits non-zero for missing issues, which would abort the script under `set -euo pipefail`. The empty string fallback is the skip signal.
- If the input string is empty or produces no valid items after parsing, the script should output `{"issues": []}` and let the caller decide whether that is an error.
