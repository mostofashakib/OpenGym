#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/opt/homebrew/opt/python@3.11/bin/python3.11"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

echo "========================================================"
echo " Apex Enterprise Cloud UI Environment Audit"
echo "========================================================"
echo "Checking Bridge State Hash..."
"$PYTHON_BIN" "$DIR/scripts/enterprise_bridge.py" state_hash

echo ""
echo "Recent Enterprise Audit Events:"
"$PYTHON_BIN" "$DIR/scripts/enterprise_bridge.py" get_audit_log "" ""
