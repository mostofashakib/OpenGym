"""Client library for interacting with the browser environment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from browser_sim.protocol import request
from browser_sim.service import execute_tool, export_state
from browser_sim.sqlite_common import get_connection


class BrowserClient:
    def __init__(
        self,
        socket_path: str | None = None,
        db_path: str | Path | None = None,
    ) -> None:
        self.socket_path = socket_path or os.environ.get("BROWSER_SOCKET", "/run/browser/agent.sock")
        self.db_path = db_path or os.environ.get("BROWSER_DB")

    def execute_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if os.path.exists(self.socket_path):
            try:
                resp = request(self.socket_path, {"op": "call_tool", "tool": name, "args": args})
                if resp.get("ok"):
                    return {"ok": True, "result": resp.get("result", {})}
                return {"ok": False, "error": resp.get("error", "Unknown error")}
            except Exception:
                pass

        candidate_dbs = [
            self.db_path,
            Path("/var/lib/browser/browser.db"),
            Path("/tmp/test_browser.db"),
            Path("browser.db"),
        ]
        for cand in candidate_dbs:
            if cand and Path(cand).exists():
                res = execute_tool(cand, name, args)
                return {"ok": "error" not in res, "result": res}

        return {"ok": False, "error": "Cannot connect to browser socket or database"}

    def navigate(self, url: str) -> dict[str, Any]:
        return self.execute_tool("navigate", {"url": url})

    def get_page(self) -> dict[str, Any]:
        return self.execute_tool("get_page", {})

    def click(self, element_id: str) -> dict[str, Any]:
        return self.execute_tool("click", {"element_id": element_id})

    def type_text(self, element_id: str, text: str) -> dict[str, Any]:
        return self.execute_tool("type_text", {"element_id": element_id, "text": text})

    def select_option(self, element_id: str, value: str) -> dict[str, Any]:
        return self.execute_tool("select_option", {"element_id": element_id, "value": value})

    def submit_form(self, form_id: str) -> dict[str, Any]:
        return self.execute_tool("submit_form", {"form_id": form_id})

    def go_back(self) -> dict[str, Any]:
        return self.execute_tool("go_back", {})

    def submit_task(self, summary: str, audited_ids: list[str]) -> dict[str, Any]:
        return self.execute_tool("submit_task", {"summary": summary, "audited_ids": audited_ids})

    def get_state(self) -> dict[str, Any]:
        candidate_dbs = [
            self.db_path,
            Path("/var/lib/browser/browser.db"),
            Path("/tmp/test_browser.db"),
            Path("browser.db"),
        ]
        for cand in candidate_dbs:
            if cand and Path(cand).exists():
                with get_connection(cand) as conn:
                    return {"ok": True, "result": export_state(conn)}
        return {"ok": False, "error": "No database found for state export"}
