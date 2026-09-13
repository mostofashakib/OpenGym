#!/usr/bin/env bash
# Terminate any running software simulation or MCP server instances.
set -euo pipefail

echo "Stopping Software Environment background processes..."
pkill -f "software_sim.mcp_server" 2>/dev/null || true
pkill -f "software-mcp" 2>/dev/null || true

# Cleanup temporary SQLite databases if desired
rm -f /tmp/software_sim.db /tmp/software_sim.db-wal /tmp/software_sim.db-shm 2>/dev/null || true

echo "Software environment stopped."
