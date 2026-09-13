#!/usr/bin/env bash
set -e

PORT=3005
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Apex Enterprise Cloud UI on port ${PORT}..."
cd "${DIR}"

# Kill any existing instance on port 3005
lsof -ti :${PORT} | xargs kill -9 2>/dev/null || true

export FIXED_TIME_ENABLED=true
export FIXED_TIME_ISO="2026-10-15T09:00:00Z"
export NODE_OPTIONS="--require ./fake-time.js"

# Run Next.js server in development mode
exec npx next dev -p ${PORT}
