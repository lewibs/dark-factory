#!/bin/bash
# Usage: reopen-remote-control.sh <remote-control-name>
# Opens a new terminal in the current directory running Claude in remote-control mode,
# then closes this (the installer) terminal.

NAME="${1:-dark factory}"

# Open a new terminal with the given name
bash "$(dirname "$0")/open-factory.sh" "$NAME"
OPEN_EXIT=$?

if [ $OPEN_EXIT -ne 0 ]; then
    exit $OPEN_EXIT
fi

# Close the current terminal
bash "$(dirname "$0")/close-factory.sh"
