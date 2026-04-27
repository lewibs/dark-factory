---
name: bash-associative-array-pipe-delimited
description: "Use pipe-delimited strings in bash associative arrays to map a key to multiple values, then split with IFS='|' read -ra when consuming."
user-invocable: false
---
## When to use

When you need a bash associative array that maps a string key to a list of
values (e.g., agent name → list of checklist items). Bash does not support
arrays as associative array values, so a pipe-delimited string is the standard
workaround.

## Steps

1. Declare the associative array and populate each key with a pipe-delimited
   string of values:
   ```bash
   declare -A MY_MAP
   MY_MAP["key-one"]="item a|item b|item c"
   MY_MAP["key-two"]="step 1|step 2"
   ```

2. Look up a key and check whether it exists:
   ```bash
   KEY="key-one"
   if [[ -n "${MY_MAP[$KEY]:-}" ]]; then
     echo "found"
   fi
   ```
   The `:-` default prevents an unbound-variable error when the key is absent.

3. Split the pipe-delimited string into a bash array:
   ```bash
   IFS='|' read -ra ITEMS <<< "${MY_MAP[$KEY]}"
   ```
   `ITEMS` is now a regular indexed array: `("item a" "item b" "item c")`.

4. Iterate over the split values:
   ```bash
   for item in "${ITEMS[@]}"; do
     echo "$item"
   done
   ```

## Notes

- Choose `|` as the delimiter only when you are certain the values themselves
  will never contain a literal `|`. If values may contain pipes, choose a
  different delimiter (e.g., `^^` or `\x1F`) and adjust the `IFS` assignment
  accordingly.
- `IFS='|' read -ra ITEMS <<< "$str"` is a local IFS assignment — it does not
  permanently alter the shell's IFS, so no restore is needed.
- This pattern is used in `agents/dark-factory/scripts/pre-tool-use-hook.sh`
  to map agent names to their checklist items.
