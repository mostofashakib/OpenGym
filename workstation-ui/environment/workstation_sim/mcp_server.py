"""FastMCP / JSON-RPC 2.0 stdio server providing Workstation tools to agents."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from workstation_sim.context import WorkstationContext
from workstation_sim.tool_definitions import TOOL_DEFINITIONS

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "workstation", "version": "1.0.0"}


def tool_list() -> list[dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "inputSchema": tool["parameters"],
        }
        for tool in TOOL_DEFINITIONS
    ]


def _response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def _tool_result(result_data: dict[str, Any], is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(result_data, sort_keys=True, default=str)}],
        "isError": is_error,
    }


def handle_request(
    ctx: WorkstationContext,
    req: dict[str, Any],
) -> dict[str, Any] | None:
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return _response(
            msg_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        )
    elif method in ("notifications/initialized", "initialized"):
        return None
    elif method == "ping":
        return _response(msg_id, {})
    elif method == "tools/list":
        return _response(msg_id, {"tools": tool_list()})
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        try:
            res = ctx.execute_tool(name, args)
            return _response(msg_id, _tool_result(res))
        except Exception as exc:
            return _response(msg_id, _tool_result({"error": str(exc)}, is_error=True))
    else:
        return _error(msg_id, -32601, f"Method '{method}' not found")


def serve_stdio(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> None:
    ctx = WorkstationContext.from_env()
    ctx.ensure_initialized()

    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as exc:
            stdout.write(json.dumps(_error(None, -32700, f"Parse error: {exc}")) + "\n")
            stdout.flush()
            continue

        resp = handle_request(ctx, req)
        if resp is not None:
            stdout.write(json.dumps(resp) + "\n")
            stdout.flush()


if __name__ == "__main__":
    serve_stdio()
