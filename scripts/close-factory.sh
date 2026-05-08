#!/bin/bash
# Usage: close-factory.sh
# Closes the current terminal/factory session only.

# Find this terminal tab's vte-spawn scope from the cgroup
SCOPE=$(grep -oP 'vte-spawn-[^/]+\.scope' /proc/$$/cgroup 2>/dev/null | head -1)

if [ -n "$SCOPE" ]; then
    systemctl --user stop "$SCOPE" 2>/dev/null || true
fi

# Also kill the claude process so the old session fully terminates
pid=$$
while [ "$pid" -gt 1 ]; do
    ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
    name=$(ps -o comm= -p "$pid" 2>/dev/null | tr -d ' ')
    if [ "$name" = "claude" ]; then
        kill "$pid" 2>/dev/null || true
        break
    fi
    [ -z "$ppid" ] || [ "$ppid" -le 1 ] && break
    pid=$ppid
done
