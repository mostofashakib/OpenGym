#!/usr/bin/env bash
# Open Harbor trial viewer for software environment jobs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOBS_PATH="$SCRIPT_DIR/jobs/harbor"

if [ ! -d "$JOBS_PATH" ]; then
  echo "No Harbor jobs directory found at $JOBS_PATH"
  exit 1
fi

exec harbor view "$JOBS_PATH" "$@"
