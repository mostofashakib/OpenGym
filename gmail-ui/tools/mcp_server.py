"""MCP server that hands Gmail environment tools to the agent's harness.

Harbor registers this from `task.toml` (`[[environment.mcp_servers]]`), so
the Gmail workspace arrives in the agent's own tool list with schemas
before the first turn.

Protocol: newline-delimited JSON-RPC 2.0 on stdin/stdout.
"""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from tools.gmail_client import GmailClient
from tools.tool_definitions import get_tool_definitions

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


def _error(message_id: Any, code: int, message: str, data: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        payload["data"] = data
    return {"jsonrpc": "2.0", "id": message_id, "error": payload}


def _negotiate_version(requested: Any) -> str:
    if isinstance(requested, str) and requested in SUPPORTED_PROTOCOL_VERSIONS:
        return requested
    return PROTOCOL_VERSION


def dispatch(
    message: dict[str, Any],
    client: GmailClient,
) -> dict[str, Any] | None:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(message.get("id"), INVALID_REQUEST, "Invalid JSON-RPC 2.0 request.")

    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}

    # Notification (no id) -> do not reply
    if msg_id is None:
        return None

    if method == "initialize":
        return _response(
            msg_id,
            {
                "protocolVersion": _negotiate_version(params.get("protocolVersion")),
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            },
        )

    if method == "ping":
        return _response(msg_id, {})

    if method == "tools/list":
        return _response(msg_id, {"tools": tool_list()})

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments") or {}
        if not isinstance(tool_name, str):
            return _error(msg_id, INVALID_PARAMS, "`name` must be a string.")
        if not isinstance(arguments, dict):
            return _error(msg_id, INVALID_PARAMS, "`arguments` must be an object.")

        envelope = client.execute_tool(tool_name, arguments)
        return _response(
            msg_id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(envelope, sort_keys=True),
                    }
                ],
                "isError": not envelope.get("ok", True),
            },
        )

    return _error(msg_id, METHOD_NOT_FOUND, f"Method not found: {method}")


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> None:
    client = GmailClient()
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            reply = _error(None, PARSE_ERROR, f"Parse error: {exc}")
            stdout.write(json.dumps(reply) + "\n")
            stdout.flush()
            continue

        res = dispatch(req, client)
        if res is not None:
            stdout.write(json.dumps(res) + "\n")
            stdout.flush()


if __name__ == "__main__":
    serve()
