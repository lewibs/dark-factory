#!/bin/bash
# Usage: close-factory.sh <remote-control-name>
# Kills all other running Claude terminals and spawns one fresh factory terminal.
# Safe by design: only terminals whose process tree contains a `claude` descendant are targeted.
# The calling terminal (this one) is left untouched and not killed.

NAME="${1:-dark factory}"

# Get the PID of this terminal's main scope
get_own_scope_pid() {
    # Find all cgroup scopes for the current process
    if [ -f /proc/$$/cgroup ]; then
        grep -oP 'vte-spawn-[^/]+\.scope' /proc/$$/cgroup 2>/dev/null | head -1
    fi
}

# Find all Claude terminal scope PIDs (excluding our own)
find_claude_scope_terminals() {
    local own_scope
    own_scope="$(get_own_scope_pid)"

    # Find all systemd user service scopes related to terminal emulators
    systemctl --user list-units --state running --no-pager 2>/dev/null | grep -oP 'vte-spawn-[^/]+\.scope' | while read -r scope; do
        # Skip our own scope
        if [ "$scope" != "$own_scope" ]; then
            # Check if this scope has a claude process running inside
            local pids
            pids=$(systemctl --user show -p MainPID,ControlGroup "$scope" 2>/dev/null | grep MainPID | grep -oP '\d+')
            if [ -n "$pids" ]; then
                # Check if any process in this scope has 'claude' in its ancestry
                for pid in $pids; do
                    local check_pid=$pid
                    while [ "$check_pid" -gt 1 ]; do
                        local pname
                        pname=$(ps -o comm= -p "$check_pid" 2>/dev/null | tr -d ' ')
                        if [ "$pname" = "claude" ]; then
                            echo "$scope"
                            break 2
                        fi
                        local ppid
                        ppid=$(ps -o ppid= -p "$check_pid" 2>/dev/null | tr -d ' ')
                        [ -z "$ppid" ] || [ "$ppid" -le 1 ] && break
                        check_pid=$ppid
                    done
                done
            fi
        fi
    done
}

# Function to open a new terminal with fallback support
open_terminal() {
    local cmd="claude \"/remote-control $NAME\""
    local cwd
    cwd="$(pwd)"

    # Try gnome-terminal first (GNOME desktop)
    if command -v gnome-terminal &>/dev/null; then
        gnome-terminal --working-directory="$cwd" -- bash -c "$cmd"
        return $?
    fi

    # Fallback to x-terminal-emulator (Debian/Ubuntu standard)
    if command -v x-terminal-emulator &>/dev/null; then
        ( cd "$cwd" && x-terminal-emulator -e bash -c "$cmd" )
        return $?
    fi

    # Fallback to xterm
    if command -v xterm &>/dev/null; then
        ( cd "$cwd" && xterm -e bash -c "$cmd" )
        return $?
    fi

    # Fallback to konsole (KDE)
    if command -v konsole &>/dev/null; then
        konsole --workdir "$cwd" -e bash -c "$cmd"
        return $?
    fi

    # No terminal emulator found
    echo "Error: No terminal emulator found (tried: gnome-terminal, x-terminal-emulator, xterm, konsole)" >&2
    return 1
}

# Kill all other Claude terminals
kill_other_terminals() {
    local killed_any=0
    find_claude_scope_terminals | while read -r scope; do
        systemctl --user stop "$scope" 2>/dev/null || true
        killed_any=1
    done
    return $killed_any
}

# Main flow
kill_other_terminals
KILL_EXIT=$?

# Spawn new factory terminal regardless of kill result
open_terminal
TERMINAL_EXIT=$?

if [ $TERMINAL_EXIT -ne 0 ]; then
    echo "Error: Failed to open terminal (exit code: $TERMINAL_EXIT)" >&2
    exit $TERMINAL_EXIT
fi

exit 0
