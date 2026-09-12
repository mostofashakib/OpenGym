"""An MCP server that hands the Gmail environment to the agent's harness.

Harbor registers this from task.toml ([[environment.mcp_servers]]), so
the tools arrive in the agent's tool list, with each tool's schema,
before the first turn. Nothing in the task prompt has to explain that a Gmail
interface exists or how to drive it -- discovering the workspace is the harness's
job, and what is in the workspace is the agent's.

This is a client. It holds no state, owns no database, and imports neither the
service nor the seed: every call travels over agent.sock to the container
that does. Speaking MCP rather than a private protocol is what makes the surface
portable across harnesses; speaking it over stdio is what keeps it working under
an environment with no network.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from gmail_sim.protocol import AGENT_SOCKET, request
from gmail_sim.tool_definitions import get_tool_definitions

PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INFO = {"name": "gmail", "version": "1.0.0"}

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602


def tool_list() -> list[dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["input_schema"],
        }
        for tool in get_tool_definitions()
    ]


def _response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def _tool_result(envelope: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(
            envelope, separators=(",", ":"), sort_keys=True,
        )}],
        "isError": not envelope.get("ok", False),
    }


def _call_tool(socket_path: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        envelope = request(socket_path, {"op": "call_tool", "tool": name, "input": arguments})
    except OSError as exc:
        envelope = {
            "ok": False,
            "error": {
                "code": "service_unavailable",
                "type": "unavailable",
                "message": f"Cannot reach the Gmail simulator: {exc}",
            },
        }
    return _tool_result(envelope)


def dispatch(message: dict[str, Any], socket_path: str = AGENT_SOCKET) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    is_notification = "id" not in message

    if not isinstance(method, str):
        return None if is_notification else _error(message_id, INVALID_REQUEST, "Missing method.")
    if is_notification:
        return None

    params = message.get("params") or {}
    if not isinstance(params, dict):
        return _error(message_id, INVALID_PARAMS, "params must be an object.")

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
    if method == "ping":
        return _response(message_id, {})
    if method == "tools/list":
        return _response(message_id, {"tools": tool_list()})
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str) or not name:
            return _error(message_id, INVALID_PARAMS, "tools/call requires a tool name.")
        name = name.removeprefix("gmail_").removeprefix("gmail.").removeprefix("gmail__")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _error(message_id, INVALID_PARAMS, "arguments must be an object.")
        return _response(message_id, _call_tool(socket_path, name, arguments))

    return _error(message_id, METHOD_NOT_FOUND, f"Unknown method: {method}")


def serve(stdin: TextIO, stdout: TextIO, socket_path: str = AGENT_SOCKET) -> int:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            response: dict[str, Any] | None = _error(None, PARSE_ERROR, f"Malformed frame: {exc}")
        else:
            if not isinstance(message, dict):
                response = _error(None, INVALID_REQUEST, "A frame must be a JSON object.")
            else:
                response = dispatch(message, socket_path)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    socket_path = argv[1] if len(argv) > 1 and argv[0] == "--socket" else AGENT_SOCKET
    return serve(sys.stdin, sys.stdout, socket_path)


if __name__ == "__main__":
    raise SystemExit(main())
