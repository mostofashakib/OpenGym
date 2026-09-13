#!/usr/bin/env bash
set -euo pipefail

echo "Stopping workstation-ui dev server on port 3008..."
lsof -ti :3008 | xargs kill -9 2>/dev/null || true
echo "workstation-ui stopped."
