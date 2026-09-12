"""MCP server entrypoint for browser tools."""

from __future__ import annotations

from browser_sim.mcp_server import serve_stdio

if __name__ == "__main__":
    serve_stdio()
