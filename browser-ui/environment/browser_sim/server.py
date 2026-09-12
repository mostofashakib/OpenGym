"""Unix socket server daemon for browser environment."""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
from pathlib import Path
from typing import Any

from browser_sim.clock import VIRTUAL_CLOCK
from browser_sim.protocol import recv_json, send_json
from browser_sim.seed import seed_database
from browser_sim.service import BrowserService, export_state
from browser_sim.sqlite_common import get_connection


class UnixSocketServer:
    def __init__(self, db_path: Path | str, socket_path: str, is_admin: bool = False) -> None:
        self.db_path = db_path
        self.socket_path = socket_path
        self.is_admin = is_admin
        self._running = False
        self._sock: socket.socket | None = None

    def start(self) -> None:
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(self.socket_path)
        os.chmod(self.socket_path, 0o777)
        self._sock.listen(10)
        self._running = True

        while self._running:
            try:
                client, _ = self._sock.accept()
                t = threading.Thread(target=self._handle_client, args=(client,), daemon=True)
                t.start()
            except Exception:
                if not self._running:
                    break

    def stop(self) -> None:
        self._running = False
        if self._sock:
            self._sock.close()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

    def _handle_client(self, client: socket.socket) -> None:
        with client:
            while True:
                req = recv_json(client)
                if not req:
                    break
                resp = self._dispatch(req)
                send_json(client, resp)

    def _dispatch(self, req: dict[str, Any]) -> dict[str, Any]:
        op = req.get("op", "tool")
        tool = req.get("tool")
        args = req.get("args", {})

        with get_connection(self.db_path) as conn:
            svc = BrowserService(conn)

            if op == "ping":
                return {"ok": True, "result": "pong"}

            if self.is_admin:
                if op == "export_state":
                    return {"ok": True, "result": export_state(conn)}
                elif op == "reset":
                    seed_database(self.db_path)
                    return {"ok": True, "result": "reset_complete"}

            if tool:
                res = svc.execute_tool(tool, args)
                return {"ok": "error" not in res, "result": res}

            return {"ok": False, "error": f"Unknown operation or tool: {req}"}


def run_daemon(
    db_path: Path | str = "/var/lib/browser/browser.db",
    agent_socket: str = "/run/browser/agent.sock",
    admin_socket: str = "/run/browser/admin.sock",
) -> None:
    seed_database(db_path)

    agent_srv = UnixSocketServer(db_path, agent_socket, is_admin=False)
    admin_srv = UnixSocketServer(db_path, admin_socket, is_admin=True)

    t_admin = threading.Thread(target=admin_srv.start, daemon=True)
    t_admin.start()

    print(f"Browser daemon started on {agent_socket} and {admin_socket}")
    try:
        agent_srv.start()
    except KeyboardInterrupt:
        agent_srv.stop()
        admin_srv.stop()


if __name__ == "__main__":
    db = os.environ.get("BROWSER_DB", "/var/lib/browser/browser.db")
    agent_sock = os.environ.get("BROWSER_SOCKET", "/run/browser/agent.sock")
    admin_sock = os.environ.get("BROWSER_ADMIN_SOCKET", "/run/browser/admin.sock")
    run_daemon(db, agent_sock, admin_sock)
