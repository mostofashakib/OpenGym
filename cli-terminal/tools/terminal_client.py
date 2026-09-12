"""Client library for interacting with the terminal environment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from terminal_sim.protocol import request
from terminal_sim.service import execute_tool, export_state
from terminal_sim.sqlite_common import get_connection


class TerminalClient:
    def __init__(
        self,
        socket_path: str | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        self.socket_path = socket_path or os.environ.get("TERMINAL_SOCKET", "/run/terminal/agent.sock")
        self.db_path = db_path or os.environ.get("TERMINAL_DB")

    def execute_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if os.path.exists(self.socket_path):
            try:
                resp = request(self.socket_path, {"op": "call_tool", "tool": name, "args": args})
                if resp.get("ok"):
                    return {"ok": True, "result": resp.get("result", {})}
                return {"ok": False, "error": resp.get("error", "Unknown error")}
            except Exception:
                pass

        # Fallback to direct DB execution
        candidate_dbs = [
            self.db_path,
            Path("/var/lib/terminal/terminal.db"),
            Path("/tmp/test_terminal.db"),
            Path("terminal.db"),
        ]
        for cand in candidate_dbs:
            if cand and Path(cand).exists():
                res = execute_tool(cand, name, args)
                return {"ok": "error" not in res, "result": res}

        return {"ok": False, "error": "Cannot connect to socket or database"}

    def run_command(self, command: str, cwd: str = "/home/admin") -> dict[str, Any]:
        return self.execute_tool("run_command", {"command": command, "cwd": cwd})

    def read_file(self, path: str, offset: int = 0, limit: int = 100) -> dict[str, Any]:
        return self.execute_tool("read_file", {"path": path, "offset": offset, "limit": limit})

    def write_file(self, path: str, content: str, mode: str = "write") -> dict[str, Any]:
        return self.execute_tool("write_file", {"path": path, "content": content, "mode": mode})

    def list_processes(self, status: str | None = None) -> dict[str, Any]:
        args = {"status": status} if status else {}
        return self.execute_tool("list_processes", args)

    def inspect_system(self) -> dict[str, Any]:
        return self.execute_tool("inspect_system", {})

    def submit_task(self, summary: str, actions_taken: list[str]) -> dict[str, Any]:
        return self.execute_tool("submit_task", {"summary": summary, "actions_taken": actions_taken})

    def get_state(self) -> dict[str, Any]:
        candidate_dbs = [
            self.db_path,
            Path("/var/lib/terminal/terminal.db"),
            Path("/tmp/test_terminal.db"),
            Path("terminal.db"),
        ]
        for cand in candidate_dbs:
            if cand and Path(cand).exists():
                with get_connection(cand) as conn:
                    return {"ok": True, "result": export_state(conn)}
        return {"ok": False, "error": "No database found for state export"}
