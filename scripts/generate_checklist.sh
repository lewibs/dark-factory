#!/usr/bin/env bash
# generate_checklist.sh "item1" "item2" ...
# Outputs: {"todos":[{"id":"1","content":"item1","status":"pending"},...]}

items=("$@")
printf '{"todos":['
for i in "${!items[@]}"; do
  id=$((i + 1))
  content="${items[$i]}"
  encoded=$(printf '%s' "$content" | sed 's/\\/\\\\/g; s/"/\\"/g')
  if [ $i -gt 0 ]; then printf ','; fi
  printf '{"id":"%d","content":"%s","status":"pending"}' "$id" "$encoded"
done
printf ']}'
