#!/bin/bash
# Usage: reopen-remote-control.sh <remote-control-name>
# Opens a new terminal in the current directory running Claude in remote-control mode.

NAME="${1:-dark factory}"
gnome-terminal --working-directory="$(pwd)" -- bash -c "claude \"/remote-control $NAME\""
