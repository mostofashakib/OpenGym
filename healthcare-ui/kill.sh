#!/usr/bin/env bash
set -euo pipefail

echo "Stopping healthcare-ui dev server on port 3007..."
lsof -ti :3007 | xargs kill -9 2>/dev/null || true
echo "healthcare-ui stopped."
