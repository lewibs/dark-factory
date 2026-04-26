#!/usr/bin/env bash
set -euo pipefail

# Resolve the repo root (the directory containing this script's grandparent).
# Works regardless of where the repo was cloned.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "Registering dark-factory marketplace from: $PLUGIN_ROOT"
claude plugin marketplace add "$PLUGIN_ROOT"

echo "Installing dark-factory plugin..."
claude plugin install dark-factory

echo "Done. Run 'claude plugin list' to verify."
