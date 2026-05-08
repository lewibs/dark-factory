#!/bin/bash
# Usage: destroy-factories.sh
# Kills all terminal emulator windows that have a claude descendant (except our own
# window).
# Platform: Linux/GNOME. Uses vte-spawn cgroup scopes to identify individual
# gnome-terminal windows — not the shared gnome-terminal-server daemon PID.

# ── log helper ─────────────────────────────────────────────────────────────────
# Usage: _log <flow> <step> <data>
_log() {
    echo "destroy-factories | $1 | $2 | $3" >&2
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

# ── all_vte_scopes ──────────────────────────────────────────────────────────────
# Print one vte-spawn-*.scope name per line for every active gnome-terminal window.
# Each gnome-terminal window/tab has a unique vte-spawn-<uuid>.scope in the user's
# systemd session. This avoids relying on the shared gnome-terminal-server daemon PID.
all_vte_scopes() {
    systemctl --user list-units --type=scope --no-legend --no-pager 'vte-spawn-*' 2>/dev/null \
        | awk '{print $1}'
}

# ── scope_main_pid ──────────────────────────────────────────────────────────────
# Print the main PID for a given systemd scope unit, or "" if not found.
scope_main_pid() {
    local scope="$1"
    systemctl --user show "$scope" --property=MainPID --value 2>/dev/null | grep -v '^0$'
}

# ── find_claude_scope_terminals ────────────────────────────────────────────────
# Print one scope name per line for each vte-spawn scope that has a claude
# descendant, excluding our own scope.
#
# Design: enumerate by vte-spawn SCOPE (not by gnome-terminal-server daemon PID).
# All gnome-terminal windows share one gnome-terminal-server PID; targeting by
# daemon PID would cause the own-ancestor exclusion to skip every window.
# Scope-based targeting identifies each window individually.
find_claude_scope_terminals() {
    # Identify this terminal's own scope from its cgroup entry
    local SELF_SCOPE
    SELF_SCOPE=$(grep -oP 'vte-spawn-[^/]+\.scope' /proc/"$$"/cgroup 2>/dev/null | head -1)

    _log "find_claude_scope_terminals" "entry" "self_scope=${SELF_SCOPE:-none}"

    for scope in $(all_vte_scopes); do
        # Never target our own scope
        if [ -n "$SELF_SCOPE" ] && [ "$scope" = "$SELF_SCOPE" ]; then
            _log "find_claude_scope_terminals" "skip_own_scope" "scope=$scope"
            continue
        fi

        # Get the main PID for this scope and check for a claude descendant
        local main_pid
        main_pid=$(scope_main_pid "$scope")
        if [ -z "$main_pid" ]; then
            _log "find_claude_scope_terminals" "no_main_pid" "scope=$scope"
            continue
        fi

        if has_claude_descendant "$main_pid"; then
            _log "find_claude_scope_terminals" "found" "scope=$scope main_pid=$main_pid"
            echo "$scope"
        fi
    done
}

# ── find_claude_terminals (fallback for non-GNOME / non-scope systems) ─────────
# Print one terminal PID per line for each terminal emulator that has a claude
# descendant. Used on systems where vte-spawn scopes are unavailable.
find_claude_terminals() {
    local known_terms="xterm konsole x-terminal-emulator"
    local own_pid=$$

    _log "find_claude_terminals" "entry" "own_pid=$own_pid"

    for term in $known_terms; do
        for terminal_pid in $(pgrep -x "$term" 2>/dev/null); do
            # Basic self-exclusion: skip if this PID is in our own ancestry
            if [ "$terminal_pid" = "$own_pid" ]; then
                continue
            fi
            if has_claude_descendant "$terminal_pid"; then
                _log "find_claude_terminals" "found" "pid=$terminal_pid"
                echo "$terminal_pid"
            fi
        done
    done
}

# ── Kill all other Claude terminals ────────────────────────────────────────────
_log "destroy-factories" "entry"

KILLED=0

# Primary path: scope-based targeting for GNOME (vte-spawn scopes)
for scope in $(find_claude_scope_terminals); do
    _log "destroy-factories" "stop_scope" "scope=$scope"
    systemctl --user stop "$scope" 2>/dev/null || {
        echo "Warning: could not stop scope $scope" >&2
        _log "destroy-factories" "kill_failed" "scope=$scope"
    }
    KILLED=$((KILLED + 1))
done

# Fallback path: PID-based kill for non-GNOME terminals (xterm, konsole, etc.)
for pid in $(find_claude_terminals); do
    _log "destroy-factories" "kill" "pid=$pid"
    kill "$pid" 2>/dev/null || {
        echo "Warning: could not kill terminal PID $pid" >&2
        _log "destroy-factories" "kill_failed" "pid=$pid"
    }
    KILLED=$((KILLED + 1))
done

_log "destroy-factories" "done" "terminals_killed=$KILLED"
exit 0
