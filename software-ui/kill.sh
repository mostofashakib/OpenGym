#!/usr/bin/env bash
set -euo pipefail

echo "Stopping software-ui dev server on port 3006..."
lsof -ti :3006 | xargs kill -9 2>/dev/null || true
echo "software-ui stopped."
