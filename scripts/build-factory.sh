#!/bin/bash
# Usage: build-factory.sh <remote-control-name>
# Opens a new terminal window running Claude in remote-control mode.
# The calling terminal is left completely untouched.

NAME="${1:-dark factory}"

# Delegate to open-factory.sh
bash "$(dirname "$0")/open-factory.sh" "$NAME"
exit $?
