#!/usr/bin/env bash
set -e

# Test runner for Healthcare Agent Simulation Environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEALTHCARE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${HEALTHCARE_DIR}/.." && pwd)"

export PYTHONPATH="${WORKSPACE_ROOT}:${HEALTHCARE_DIR}/environment:${PYTHONPATH}"

echo "========================================================"
echo " Running Healthcare Agent Simulation Test Suite"
echo " Workspace Root: ${WORKSPACE_ROOT}"
echo "========================================================"

PYTHON_BIN="python3"
if command -v /opt/homebrew/bin/python3.11 &>/dev/null; then
  PYTHON_BIN="/opt/homebrew/bin/python3.11"
fi

"${PYTHON_BIN}" -m pytest "${HEALTHCARE_DIR}/tests" -v "$@"

echo "========================================================"
echo " All Healthcare Environment tests passed successfully! "
echo "========================================================"
