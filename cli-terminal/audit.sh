#!/usr/bin/env bash
# Audit the grader over already-graded terminal trials.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/environment:$SCRIPT_DIR/tools:${PYTHONPATH:-}"

if [[ $# -lt 1 ]]; then
  echo "usage: $(basename "$0") <trial-dir>" >&2
  exit 2
fi

exec python3 "$SCRIPT_DIR/tools/grader_audit.py" "$@"
