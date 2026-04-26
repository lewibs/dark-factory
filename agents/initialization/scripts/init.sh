#!/usr/bin/env bash
set -euo pipefail

GITHUB_URL="${1:-}"

if [ -n "$GITHUB_URL" ]; then
    REPO_NAME=$(basename "$GITHUB_URL" .git)

    if [ -d "$REPO_NAME" ]; then
        echo "Error: directory '$REPO_NAME' already exists." >&2
        exit 1
    fi

    mkdir "$REPO_NAME"
    cd "$REPO_NAME"
    git clone "$GITHUB_URL"
    echo "PROJECT_PATH=${REPO_NAME}/${REPO_NAME}"
else
    DIRNAME=$(basename "$PWD")

    if [ -d "$DIRNAME" ]; then
        echo "Error: subdirectory '$DIRNAME' already exists in $(pwd)." >&2
        exit 1
    fi

    mkdir "$DIRNAME"

    find . -maxdepth 1 ! -name '.' ! -name "$DIRNAME" -exec mv {} "$DIRNAME/" \;
    echo "PROJECT_PATH=${DIRNAME}/${DIRNAME}"
fi
