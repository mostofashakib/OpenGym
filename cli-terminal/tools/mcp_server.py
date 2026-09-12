"""MCP server entrypoint for tools package."""

from __future__ import annotations

from terminal_sim.mcp_server import serve_stdio

if __name__ == "__main__":
    serve_stdio()
