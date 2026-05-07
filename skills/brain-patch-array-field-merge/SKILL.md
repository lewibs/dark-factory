---
name: brain-patch-array-field-merge
description: "When a brain-patch.json contains an array field (e.g. notes, artifacts), the post-hook must concatenate rather than overwrite — jq object-merge (*) silently replaces arrays."
user-invocable: false
learned-skill: true
---
## When to use

Whenever a new array-typed field is added to brain.json (e.g. `notes`, `artifactsCreated`, `warnings`) and multiple sub-agents are expected to append to it via brain-patch.json. The standard `jq -s '.[0] * .[1]'` object-merge replaces arrays wholesale — successive patches would lose all prior entries.

## Steps

1. In brain.json initialization, declare the field as an empty array:
   ```json
   { "notes": [] }
   ```

2. In sub-agent brain-patch.json output, include only the new entries to append:
   ```json
   { "notes": ["execution-agent: implemented 3 flows, modified auth.py, user.py"] }
   ```

3. In `post-tool-use-hook.sh`, detect whether the patch contains the array field and branch on it:
   ```bash
   if jq -e '.notes' "$PATCH_PATH" > /dev/null 2>&1; then
     (
       flock -x 200
       TMP=$(mktemp /tmp/brain-notes-XXXXXX.json)
       jq -s '
         (.[0].notes // []) + (.[1].notes // []) as $merged_notes |
         .[0] * .[1] | .notes = $merged_notes
       ' "$BRAIN_PATH" "$PATCH_PATH" > "$TMP" && mv "$TMP" "$BRAIN_PATH"
       rm -f "$PATCH_PATH"
     ) 200>"$BRAIN_LOCK"
   else
     # standard scalar/object merge path
     (
       flock -x 200
       TMP=$(mktemp /tmp/brain-post-XXXXXX.json)
       jq -s '.[0] * .[1]' "$BRAIN_PATH" "$PATCH_PATH" > "$TMP" \
         && mv "$TMP" "$BRAIN_PATH"
       rm -f "$PATCH_PATH"
     ) 200>"$BRAIN_LOCK"
   fi
   ```

   The jq expression works in two passes:
   - First concatenates the two arrays into `$merged_notes`
   - Then applies the standard object-merge (`*`) for all other fields
   - Finally overwrites `.notes` with the concatenated result

4. In the pre-hook, inject array contents as a prominent block above the brain state JSON so agents see accumulated notes clearly. Example for a `notes` field:
   ```bash
   NOTES_JSON=$(jq -c '.notes // []' "$BRAIN_PATH")
   NOTES_COUNT=$(printf '%s' "$NOTES_JSON" | jq 'length')
   if [ "$NOTES_COUNT" -gt 0 ]; then
     NOTES_BLOCK=$(printf '%s' "$NOTES_JSON" | jq -r '.[] | "- " + .')
     NOTES_HEADER="HANDOFF NOTES FROM PRIOR AGENTS:\n${NOTES_BLOCK}\n\n"
   else
     NOTES_HEADER=""
   fi
   NEW_PROMPT="${NOTES_HEADER}BRAIN STATE (read-only context):
   ${BRAIN_CONTEXT}
   ${CURRENT_PROMPT}"
   ```

## Notes

- The detection check (`jq -e '.notes'`) only branches when the patch actually includes a `notes` key. Patches that do not include the array field use the fast `jq -s '.[0] * .[1]'` path and are not affected.
- If multiple array fields exist in brain.json (e.g. `notes` and `artifacts`), extend the jq expression to concatenate each one before applying `*`:
  ```jq
  (.[0].notes // []) + (.[1].notes // []) as $notes |
  (.[0].artifacts // []) + (.[1].artifacts // []) as $arts |
  .[0] * .[1] | .notes = $notes | .artifacts = $arts
  ```
- Always keep the `flock` guard around the read-modify-write even in the array-merge branch — concurrent hook invocations can still race.
- The prominent injection of array contents (Step 4) is intentional: burying them inside the brain JSON blob means agents are less likely to notice them. A separate header block ensures the information is salient.
