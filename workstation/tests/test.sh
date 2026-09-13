#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/environment:$SCRIPT_DIR/tests:${PYTHONPATH:-}"

PYTHON_BIN="python3"
if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

echo "--- Running Workstation Pytest Suites ---"
if command -v pytest >/dev/null 2>&1; then
  pytest "$SCRIPT_DIR/tests" -v
else
  "$PYTHON_BIN" -m pytest "$SCRIPT_DIR/tests" -v
fi

echo "--- Running Oracle Self-Verification ---"
"$PYTHON_BIN" "$SCRIPT_DIR/solution/oracle.py"
