#!/usr/bin/env bash
# Terminate any running enterprise simulation or MCP server instances.
set -euo pipefail

echo "Stopping Enterprise Environment background processes..."
pkill -f "enterprise_sim.mcp_server" 2>/dev/null || true
pkill -f "enterprise-mcp" 2>/dev/null || true

# Cleanup temporary SQLite databases if desired
rm -f /tmp/enterprise_company.db /tmp/enterprise_company.db-wal /tmp/enterprise_company.db-shm 2>/dev/null || true

echo "Enterprise environment stopped."
