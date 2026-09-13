#!/usr/bin/env bash
# Terminate any running healthcare simulation or MCP server instances.
set -euo pipefail

echo "Stopping Healthcare Environment background processes..."
pkill -f "healthcare_sim.mcp_server" 2>/dev/null || true
pkill -f "healthcare-mcp" 2>/dev/null || true

# Cleanup temporary SQLite databases if desired
rm -f /tmp/healthcare_sim.db /tmp/healthcare_sim.db-wal /tmp/healthcare_sim.db-shm 2>/dev/null || true

echo "Healthcare environment stopped."
