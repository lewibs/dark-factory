#!/usr/bin/env bash
set -euo pipefail

# Run from the outer wrapper directory (dark_factory/).
# Usage: bash prep-feature-dir.sh <task-name>
# Prints: WORK_DIR=dark_factory-<task-name>

TASK_NAME="${1:-}"
if [ -z "$TASK_NAME" ]; then
    echo "Error: task name required. Usage: $0 <task-name>" >&2
    exit 1
fi

WORK_DIR="dark_factory-${TASK_NAME}"

if [ -d "$WORK_DIR" ]; then
    echo "Error: work directory '$WORK_DIR' already exists." >&2
    exit 1
fi

cd dark_factory
git pull origin main || { echo "Error: git pull failed." >&2; exit 1; }
cd ..

cp -r dark_factory "$WORK_DIR" || { echo "Error: cp failed." >&2; exit 1; }

echo "WORK_DIR=${WORK_DIR}"
