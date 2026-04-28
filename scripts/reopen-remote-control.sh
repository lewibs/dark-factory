#!/bin/bash
# Usage: reopen-remote-control.sh <remote-control-name>
# Opens a new terminal in the current directory running Claude in remote-control mode,
# then closes this (the installer) terminal.

NAME="${1:-dark factory}"

# Function to open a new terminal with fallback support
open_terminal() {
    local cmd="claude \"/remote-control $NAME\""
    local cwd="$(pwd)"

    # Try gnome-terminal first (GNOME desktop)
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --working-directory="$cwd" -- bash -c "$cmd"
        return $?
    fi

    # Fallback to x-terminal-emulator (Debian/Ubuntu standard)
    if command -v x-terminal-emulator &> /dev/null; then
        cd "$cwd" && x-terminal-emulator -e bash -c "$cmd"
        return $?
    fi

    # Fallback to xterm
    if command -v xterm &> /dev/null; then
        cd "$cwd" && xterm -e bash -c "$cmd"
        return $?
    fi

    # Fallback to konsole (KDE)
    if command -v konsole &> /dev/null; then
        konsole --workdir "$cwd" -e bash -c "$cmd"
        return $?
    fi

    # No terminal emulator found
    echo "Error: No terminal emulator found (tried: gnome-terminal, x-terminal-emulator, xterm, konsole)" >&2
    return 1
}

# Walk up the process tree from the current script PID to find the nearest
# ancestor whose name matches a known terminal emulator.  Kill only that one
# process and stop immediately.  If no terminal emulator is found in the tree
# (e.g. invoked from Claude Code's bash tool), skip silently.
kill_terminal_ancestor() {
    local known_terms="gnome-terminal gnome-terminal-server xterm konsole x-terminal-emulator"
    local pid=$$

    while true; do
        # Obtain the parent PID of $pid; strip leading/trailing whitespace.
        local ppid
        ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')

        # Stop if we hit an invalid/missing PPID or reach PID 1 or below.
        if [ -z "$ppid" ] || [ "$ppid" -le 1 ] 2>/dev/null; then
            break
        fi

        # Get the process name for this ancestor.
        local pname
        pname=$(ps -o comm= -p "$ppid" 2>/dev/null | tr -d ' ')

        # Check whether pname matches any known terminal emulator.
        for term in $known_terms; do
            if [ "$pname" = "$term" ]; then
                kill "$ppid" 2>/dev/null || {
                    echo "Warning: Could not close the installer terminal (PID: $ppid)" >&2
                }
                return
            fi
        done

        # Move one level up.
        pid=$ppid
    done

    # No terminal emulator ancestor found — skip silently.
}

# Launch the new terminal with Claude in remote-control mode
open_terminal
TERMINAL_EXIT=$?

# Verify the terminal was opened successfully before closing the installer terminal
if [ $TERMINAL_EXIT -eq 0 ]; then
    kill_terminal_ancestor
else
    echo "Error: Failed to open terminal (exit code: $TERMINAL_EXIT)" >&2
    exit $TERMINAL_EXIT
fi
