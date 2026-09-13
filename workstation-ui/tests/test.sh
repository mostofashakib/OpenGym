#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)"

export PYTHONPATH="${PYTHONPATH:-}:$REPO_ROOT:$REPO_ROOT/workstation:$REPO_ROOT/workstation/environment:$PROJECT_ROOT"

echo "========================================================"
echo " Running Workstation-UI Bridge & Integration Test Suite"
echo "========================================================"

PYTHON_BIN="python3"
if [ -x "/opt/homebrew/opt/python@3.11/bin/python3.11" ]; then
  PYTHON_BIN="/opt/homebrew/opt/python@3.11/bin/python3.11"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
elif [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
fi

"$PYTHON_BIN" -m pytest "$SCRIPT_DIR" -v

echo "========================================================"
echo " All Workstation-UI tests passed successfully!"
echo "========================================================"
