"""The Gmail simulation daemon: serves agent.sock and admin.sock."""

from __future__ import annotations

import argparse
import logging
import os
import socket
import socketserver
import threading
from pathlib import Path
from typing import Any

from gmail_sim.protocol import ADMIN_SOCKET, AGENT_SOCKET, decode, encode
from gmail_sim.service import (
    DEFAULT_DB_PATH,
    DEFAULT_SNAPSHOT_PATH,
    TOOL_NAMES,
    execute_tool,
    export_state,
    get_connection,
)
from gmail_sim.sqlite_common import InternalError, UnknownToolError, WorldError, storage_errors
from gmail_sim.tool_definitions import get_tool_definitions

LOGGER = logging.getLogger("gmaild")


def _from_error(exc: WorldError) -> dict[str, Any]:
    return {"ok": False, "error": {"code": exc.code, "message": exc.message}}


class SocketServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True

    def __init__(self, socket_path: str, handler_cls: type[socketserver.BaseRequestHandler], mode: int) -> None:
        self.socket_path = socket_path
        self.mode = mode
        if os.path.exists(socket_path):
            os.unlink(socket_path)
        os.makedirs(os.path.dirname(socket_path), exist_ok=True)
        super().__init__(socket_path, handler_cls)
        os.chmod(socket_path, mode)

    def server_close(self) -> None:
        super().server_close()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)


class AgentHandler(socketserver.StreamRequestHandler):
    db_path: Path

    def handle(self) -> None:
        try:
            raw = self.rfile.read()
            if not raw:
                return
            req = decode(raw)
            tool = req.get("tool")
            args = req.get("arguments") or req.get("input") or {}

            if tool == "list_tools":
                res = {"ok": True, "result": {"tools": list(get_tool_definitions())}}
            elif tool == "export_state":
                with get_connection(self.db_path) as conn:
                    res = {"ok": True, "result": export_state(conn)}
            elif tool in TOOL_NAMES:
                try:
                    res = {"ok": True, "result": execute_tool(self.db_path, tool, args)}
                except WorldError as exc:
                    res = _from_error(exc)
                except Exception as exc:
                    res = {"ok": False, "error": {"code": "internal_error", "message": str(exc)}}
            else:
                res = {"ok": False, "error": {"code": "unknown_tool", "message": f"Unknown tool '{tool}'"}}

            self.wfile.write(encode(res))
        except Exception as exc:
            LOGGER.error("Agent socket handler failed: %s", exc)


class AdminHandler(socketserver.StreamRequestHandler):
    db_path: Path

    def handle(self) -> None:
        try:
            raw = self.rfile.read()
            if not raw:
                return
            req = decode(raw)
            op = req.get("op") or req.get("tool")

            if op == "ping":
                res = {"ok": True, "result": {"status": "healthy"}}
            elif op == "export_state":
                with get_connection(self.db_path) as conn:
                    state = export_state(conn)
                res = {"ok": True, "result": state}
            elif op in TOOL_NAMES:
                args = req.get("arguments") or {}
                res = {"ok": True, "result": execute_tool(self.db_path, op, args)}
            else:
                res = {"ok": False, "error": {"code": "unknown_op", "message": f"Unknown op '{op}'"}}

            self.wfile.write(encode(res))
        except Exception as exc:
            LOGGER.error("Admin socket handler failed: %s", exc)


def serve(
    db_path: Path = DEFAULT_DB_PATH,
    agent_sock: str = AGENT_SOCKET,
    admin_sock: str = ADMIN_SOCKET,
) -> None:
    AgentHandler.db_path = db_path
    AdminHandler.db_path = db_path

    agent_srv = SocketServer(agent_sock, AgentHandler, mode=0o666)
    admin_srv = SocketServer(admin_sock, AdminHandler, mode=0o600)

    t1 = threading.Thread(target=agent_srv.serve_forever, daemon=True)
    t2 = threading.Thread(target=admin_srv.serve_forever, daemon=True)
    t1.start()
    t2.start()

    LOGGER.info("gmaild listening on %s (0666) and %s (0600)", agent_sock, admin_sock)
    try:
        t1.join()
        t2.join()
    except KeyboardInterrupt:
        pass
    finally:
        agent_srv.shutdown()
        admin_srv.shutdown()
        agent_srv.server_close()
        admin_srv.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Gmail simulation server")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT_PATH), help="Path to snapshot SQL file")
    parser.add_argument("--agent-socket", default=AGENT_SOCKET, help="Path for agent socket")
    parser.add_argument("--admin-socket", default=ADMIN_SOCKET, help="Path for admin socket")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    serve(Path(args.db), args.agent_socket, args.admin_socket)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
