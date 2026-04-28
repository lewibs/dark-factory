#!/bin/bash
# Usage: destroy-factories.sh [name]
# Kills all terminal emulator processes that have a claude descendant (except our own
# ancestor terminal), then spawns one fresh factory terminal.
# Platform: Linux. Requires one of: gnome-terminal, x-terminal-emulator, xterm, konsole.

NAME="${1:-dark factory}"

# ── log helper ─────────────────────────────────────────────────────────────────
# Usage: _log <flow> <step> <data>
_log() {
    echo "destroy-factories | $1 | $2 | $3" >&2
}

# ── open_terminal ──────────────────────────────────────────────────────────────
# Open a new terminal running claude in remote-control mode.
# Returns 0 on success, non-zero on failure.
open_terminal() {
    local cmd="claude \"/remote-control $NAME\""
    local cwd
    cwd="$(pwd)"

    _log "open_terminal" "entry" "name=$NAME cwd=$cwd"

    if command -v gnome-terminal &>/dev/null; then
        _log "open_terminal" "spawn" "emulator=gnome-terminal"
        gnome-terminal --working-directory="$cwd" -- bash -c "$cmd"
        return $?
    fi

    if command -v x-terminal-emulator &>/dev/null; then
        _log "open_terminal" "spawn" "emulator=x-terminal-emulator"
        ( cd "$cwd" && x-terminal-emulator -e bash -c "$cmd" )
        return $?
    fi

    if command -v xterm &>/dev/null; then
        _log "open_terminal" "spawn" "emulator=xterm"
        ( cd "$cwd" && xterm -e bash -c "$cmd" )
        return $?
    fi

    if command -v konsole &>/dev/null; then
        _log "open_terminal" "spawn" "emulator=konsole"
        konsole --workdir "$cwd" -e bash -c "$cmd"
        return $?
    fi

    _log "open_terminal" "error" "no_emulator_found"
    echo "Error: No terminal emulator found (tried: gnome-terminal, x-terminal-emulator, xterm, konsole)" >&2
    return 1
}

# ── all_terminal_emulator_pids ──────────────────────────────────────────────────
# Print one PID per line for every running terminal emulator process.
all_terminal_emulator_pids() {
    local known_terms="gnome-terminal gnome-terminal-server xterm konsole x-terminal-emulator"
    for term in $known_terms; do
        pgrep -x "$term" 2>/dev/null
    done | sort -u
}

# ── has_claude_descendant ───────────────────────────────────────────────────────
# Return 0 if any descendant of $1 is named "claude", non-zero otherwise.
has_claude_descendant() {
    local root_pid="$1"
    # Use pgrep to get all descendants, then check names
    local descendants
    descendants=$(pgrep -P "$root_pid" 2>/dev/null)
    for child_pid in $descendants; do
        local pname
        pname=$(ps -o comm= -p "$child_pid" 2>/dev/null | tr -d ' ')
        if [ "$pname" = "claude" ]; then
            return 0
        fi
        # Recurse into grandchildren
        if has_claude_descendant "$child_pid"; then
            return 0
        fi
    done
    return 1
}

# ── find_terminal_ancestor ─────────────────────────────────────────────────────
# Walk up the process tree from $1 and return the PID of the nearest terminal
# emulator ancestor, or "" if none found.
find_terminal_ancestor() {
    local known_terms="gnome-terminal gnome-terminal-server xterm konsole x-terminal-emulator"
    local pid="$1"

    while true; do
        local ppid
        ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')

        if [ -z "$ppid" ] || [ "$ppid" -le 1 ] 2>/dev/null; then
            echo ""
            return
        fi

        local pname
        pname=$(ps -o comm= -p "$ppid" 2>/dev/null | tr -d ' ')

        for term in $known_terms; do
            if [ "$pname" = "$term" ]; then
                echo "$ppid"
                return
            fi
        done

        pid="$ppid"
    done
}

# ── find_claude_terminals ──────────────────────────────────────────────────────
# Print one terminal PID per line for each terminal emulator that has a claude
# descendant, excluding our own ancestor terminal.
find_claude_terminals() {
    local own_ancestor_pid
    own_ancestor_pid=$(find_terminal_ancestor $$)

    _log "find_claude_terminals" "entry" "own_ancestor_pid=${own_ancestor_pid:-none}"

    for terminal_pid in $(all_terminal_emulator_pids); do
        # Never kill our own ancestor terminal
        if [ -n "$own_ancestor_pid" ] && [ "$terminal_pid" = "$own_ancestor_pid" ]; then
            _log "find_claude_terminals" "skip_own_ancestor" "pid=$terminal_pid"
            continue  # skip — this is our own terminal
        fi

        if has_claude_descendant "$terminal_pid"; then
            _log "find_claude_terminals" "found" "pid=$terminal_pid"
            echo "$terminal_pid"
        fi
    done
}

# ── Step 1 + 2: Kill all other Claude terminals ────────────────────────────────
_log "destroy-factories" "entry" "name=$NAME"

KILLED=0
for pid in $(find_claude_terminals); do
    _log "destroy-factories" "kill" "pid=$pid"
    SCOPE=$(grep -oP 'vte-spawn-[^/]+\.scope' /proc/"$pid"/cgroup 2>/dev/null | head -1)
    if [ -n "$SCOPE" ]; then
        _log "destroy-factories" "stop_scope" "pid=$pid scope=$SCOPE"
        systemctl --user stop "$SCOPE" 2>/dev/null || {
            echo "Warning: could not stop scope $SCOPE for terminal PID $pid" >&2
            _log "destroy-factories" "kill_failed" "pid=$pid scope=$SCOPE"
        }
    else
        _log "destroy-factories" "no_scope_fallback" "pid=$pid"
        kill "$pid" 2>/dev/null || {
            echo "Warning: could not kill terminal PID $pid" >&2
            _log "destroy-factories" "kill_failed" "pid=$pid"
        }
    fi
    KILLED=$((KILLED + 1))
done

_log "destroy-factories" "killed" "count=$KILLED"

# ── Step 3: Spawn fresh factory ────────────────────────────────────────────────
_log "destroy-factories" "spawn" "name=$NAME"
open_terminal || {
    echo "Error: Failed to open new factory terminal" >&2
    _log "destroy-factories" "spawn_failed" "name=$NAME"
    exit 1
}

_log "destroy-factories" "done" "terminals_killed=$KILLED"

# ── Step 4: Self-close this terminal ──────────────────────────────────────────
_log "destroy-factories" "self_close" "pid=$$"

SELF_SCOPE=$(grep -oP 'vte-spawn-[^/]+\.scope' /proc/"$$"/cgroup 2>/dev/null | head -1)
if [ -n "$SELF_SCOPE" ]; then
    systemctl --user stop "$SELF_SCOPE" 2>/dev/null || true
fi

# Also kill any claude ancestor process so the old session fully terminates
self_pid=$$
while [ "$self_pid" -gt 1 ]; do
    self_ppid=$(ps -o ppid= -p "$self_pid" 2>/dev/null | tr -d ' ')
    self_name=$(ps -o comm= -p "$self_pid" 2>/dev/null | tr -d ' ')
    if [ "$self_name" = "claude" ]; then
        kill "$self_pid" 2>/dev/null || true
        break
    fi
    ([ -z "$self_ppid" ] || [ "$self_ppid" -le 1 ]) && break
    self_pid=$self_ppid
done
