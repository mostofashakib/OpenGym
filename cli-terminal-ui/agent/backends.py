"""Where tool calls are executed for Terminal agent."""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any

from tools.terminal_client import TerminalClient
from tools.tool_definitions import get_tool_definitions


class BackendError(RuntimeError):
    """The tool backend could not be reached or failed."""


class ToolBackend(ABC):
    @abstractmethod
    async def list_tools(self) -> list[dict[str, Any]]:
        """Return the list of tool definitions."""

    @abstractmethod
    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return an envelope: {"ok": bool, "result": ...}."""

    async def aclose(self) -> None:
        return None

    def describe(self) -> dict[str, Any]:
        return {"backend": type(self).__name__}


class InProcessBackend(ToolBackend):
    def __init__(self, db_path: str = "/var/lib/terminal/terminal.db") -> None:
        self.db_path = db_path

    async def list_tools(self) -> list[dict[str, Any]]:
        return list(get_tool_definitions())

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        from terminal_sim.service import execute_tool

        try:
            res = await asyncio.to_thread(execute_tool, self.db_path, name, arguments)
            return {"ok": "error" not in res, "result": res}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


class HarborBackend(ToolBackend):
    def __init__(self, client: TerminalClient | None = None) -> None:
        self.client = client or TerminalClient()

    async def list_tools(self) -> list[dict[str, Any]]:
        return list(get_tool_definitions())

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(self.client.execute_tool, name, arguments)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


HttpBackend = HarborBackend
