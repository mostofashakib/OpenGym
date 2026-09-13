#!/usr/bin/env bash
set -e

# Test runner for Generative Software Environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOFTWARE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${SOFTWARE_DIR}/.." && pwd)"

export PYTHONPATH="${WORKSPACE_ROOT}:${PYTHONPATH}"

echo "========================================================"
echo " Running Software Environment Test Suite"
echo " Workspace Root: ${WORKSPACE_ROOT}"
echo "========================================================"

PYTHON_BIN="python3"
if command -v /opt/homebrew/bin/python3.11 &>/dev/null; then
  PYTHON_BIN="/opt/homebrew/bin/python3.11"
fi

"${PYTHON_BIN}" -m pytest "${SOFTWARE_DIR}/tests" -v "$@"

echo "========================================================"
echo " All Software Environment tests passed successfully!   "
echo "========================================================"
