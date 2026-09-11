#!/usr/bin/env bash
# Start the Harbor job viewer for this task.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOBS_PATH="$SCRIPT_DIR/jobs/harbor"

mkdir -p "$JOBS_PATH"
exec harbor view "$JOBS_PATH" "$@"
