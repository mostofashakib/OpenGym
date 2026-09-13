#!/usr/bin/env bash
set -e

# Test runner for Enterprise Agent Simulation Platform
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTERPRISE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${ENTERPRISE_DIR}/.." && pwd)"

export PYTHONPATH="${WORKSPACE_ROOT}:${ENTERPRISE_DIR}/environment:${PYTHONPATH}"

echo "========================================================"
echo " Running Enterprise Simulation Test Suite"
echo " Workspace Root: ${WORKSPACE_ROOT}"
echo "========================================================"

PYTHON_BIN="python3"
if command -v /opt/homebrew/bin/python3.11 &>/dev/null; then
  PYTHON_BIN="/opt/homebrew/bin/python3.11"
fi

"${PYTHON_BIN}" -m pytest "${ENTERPRISE_DIR}/tests" -v "$@"

echo "========================================================"
echo " All Enterprise Environment tests passed successfully! "
echo "========================================================"
