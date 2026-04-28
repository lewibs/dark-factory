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

# Launch the new terminal with Claude in remote-control mode
open_terminal
TERMINAL_EXIT=$?

# Verify the terminal was opened successfully before closing the installer terminal
if [ $TERMINAL_EXIT -eq 0 ] && [ -n "$PPID" ] && [ "$PPID" -gt 0 ] 2>/dev/null; then
    # Close the terminal that ran the install command.
    # Kill the parent process (the terminal emulator) of this shell session.
    kill "$PPID" 2>/dev/null || {
        echo "Warning: Could not close the installer terminal (PID: $PPID)" >&2
    }
else
    if [ $TERMINAL_EXIT -ne 0 ]; then
        echo "Error: Failed to open terminal (exit code: $TERMINAL_EXIT)" >&2
        exit $TERMINAL_EXIT
    fi
fi
