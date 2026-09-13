#!/usr/bin/env bash
set -uo pipefail

echo "Stopping any running Workstation processes and containers..."
pkill -f "workstation_sim.mcp_server" 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  docker ps -q --filter "name=workstation" | xargs -r docker stop 2>/dev/null || true
fi

echo "Workstation cleanup complete."
