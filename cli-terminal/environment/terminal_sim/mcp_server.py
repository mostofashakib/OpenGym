"""MCP server over stdio for the terminal environment."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, TextIO

from terminal_sim.protocol import request
from terminal_sim.tool_definitions import get_tool_definitions

PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INFO = {"name": "terminal", "version": "1.0.0"}
AGENT_SOCKET = os.environ.get("TERMINAL_SOCKET", "/run/terminal/agent.sock")


def tool_list() -> list[dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool.get("parameters", {}),
        }
        for tool in get_tool_definitions()
    ]


def _response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def _tool_result(envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(envelope, separators=(",", ":"), sort_keys=True)}],
        "isError": not envelope.get("ok", False),
    }


def _call_tool(socket_path: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    # Try socket first, fall back to direct DB if DB env is set
    try:
        envelope = request(socket_path, {"op": "call_tool", "tool": name, "args": arguments})
    except Exception as exc:
        db_path = os.environ.get("TERMINAL_DB")
        if db_path and Path(db_path).exists():
            from terminal_sim.service import execute_tool
            res = execute_tool(db_path, name, arguments)
            envelope = {"ok": "error" not in res, "result": res}
        else:
            envelope = {
                "ok": False,
                "error": f"Cannot reach terminal simulator over {socket_path}: {exc}",
            }
    return _tool_result(envelope)


def dispatch(message: dict[str, Any], socket_path: str = AGENT_SOCKET) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    is_notification = "id" not in message

    if not isinstance(method, str):
        return None if is_notification else _error(message_id, -32600, "Missing method.")
    if is_notification:
        return None

    params = message.get("params") or {}
    if not isinstance(params, dict):
        return _error(message_id, -32602, "params must be an object.")

    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
        return _response(
            message_id,
            {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return _response(message_id, {})

    if method == "tools/list":
        return _response(message_id, {"tools": tool_list()})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(name, str):
            return _error(message_id, -32602, "Missing tool name.")
        if not isinstance(arguments, dict):
            return _error(message_id, -32602, "Tool arguments must be an object.")
        return _response(message_id, _call_tool(socket_path, name, arguments))

    return _error(message_id, -32601, f"Method not found: {method}")


def serve_stdio(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    socket_path: str = AGENT_SOCKET,
) -> None:
    reader = stdin if stdin is not None else sys.stdin
    writer = stdout if stdout is not None else sys.stdout

    for raw_line in reader:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            err = _error(None, -32700, f"Parse error: {exc}")
            writer.write(json.dumps(err) + "\n")
            writer.flush()
            continue

        resp = dispatch(message, socket_path)
        if resp is not None:
            writer.write(json.dumps(resp) + "\n")
            writer.flush()


if __name__ == "__main__":
    serve_stdio()
