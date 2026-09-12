"""Where tool calls are executed.

Provides adapters for:
- Harbor environment execution (`HarborBackend`)
- Direct HTTP execution against the running Gmail server (`HttpBackend`)
- Subprocess CLI execution (`SubprocessBackend`)
"""

from __future__ import annotations

import asyncio
import json
import shlex
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from tools.gmail_client import GmailClient
from tools.tool_definitions import get_tool_definitions


class BackendError(RuntimeError):
    """The tool backend could not be reached or failed."""


class ToolBackend(ABC):
    """Abstract interface for executing Gmail actions."""

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
    """Execute tool calls directly against the authoritative Gmail simulation service."""

    def __init__(self, db_path: str = "/var/lib/gmail/gmail.db") -> None:
        self.db_path = db_path

    async def list_tools(self) -> list[dict[str, Any]]:
        from gmail_sim.tool_definitions import get_tool_definitions
        return list(get_tool_definitions())

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        from gmail_sim.service import execute_tool
        try:
            res = await asyncio.to_thread(execute_tool, self.db_path, name, arguments)
            return {"ok": True, "result": res}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def describe(self) -> dict[str, Any]:
        return {"backend": "in_process", "db": self.db_path}


class HttpBackend(ToolBackend):
    """Execute tool calls directly over HTTP via GmailClient."""

    def __init__(self, base_url: str = "http://127.0.0.1:3000", timeout_sec: float = 30.0) -> None:
        self.client = GmailClient(base_url=base_url, timeout_sec=timeout_sec)

    async def list_tools(self) -> list[dict[str, Any]]:
        return list(get_tool_definitions())

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(self.client.execute_tool, name, arguments)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def describe(self) -> dict[str, Any]:
        return {"backend": "http", "base_url": self.client.base_url}


def _parse_json_result(
    command_name: str,
    stdout: bytes | str | None,
    stderr: bytes | str | None,
    returncode: int,
) -> dict[str, Any]:
    """Extract and parse JSON payload from process output with clear error diagnostics."""
    def _to_str(val: bytes | str | None) -> str:
        if val is None:
            return ""
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="replace").strip()
        return val.strip()

    text = _to_str(stdout) or _to_str(stderr)
    if not text:
        raise BackendError(f"{command_name} exited with code {returncode} and produced no output.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise BackendError(f"{command_name} output was not valid JSON ({exc}): {text[:500]}") from exc


def _normalize_tool_definitions(raw_tools: Any) -> list[dict[str, Any]]:
    known_defs = {t["name"]: dict(t) for t in get_tool_definitions()}
    if not isinstance(raw_tools, Sequence) or isinstance(raw_tools, (str, bytes)):
        return list(get_tool_definitions())

    normalized: list[dict[str, Any]] = []
    for item in raw_tools:
        if isinstance(item, str):
            if item in known_defs:
                normalized.append(dict(known_defs[item]))
            else:
                normalized.append({
                    "name": item,
                    "description": f"Tool {item}",
                    "input_schema": {"type": "object", "properties": {}},
                })
        elif isinstance(item, Mapping):
            name = item.get("name")
            if isinstance(name, str) and name in known_defs:
                base = dict(known_defs[name])
                base.update(item)
                normalized.append(base)
            else:
                normalized.append(dict(item))
    return normalized or list(get_tool_definitions())


class SubprocessBackend(ToolBackend):
    """Drive the Gmail CLI via a subprocess."""

    def __init__(
        self,
        command: Sequence[str] | str = "gmail",
        *,
        timeout_sec: float = 120.0,
    ) -> None:
        if isinstance(command, str):
            self.command_parts = tuple(shlex.split(command))
        else:
            self.command_parts = tuple(command)
        self.timeout_sec = timeout_sec

    def describe(self) -> dict[str, Any]:
        return {"backend": "subprocess", "command": list(self.command_parts)}

    async def _run(self, argv: Sequence[str]) -> dict[str, Any]:
        cmd = [*self.command_parts, *argv]
        cmd_str = shlex.join(cmd)
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            raise BackendError(f"Could not run {cmd_str}: {exc}") from exc

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout_sec
            )
            stdout = stdout_bytes.decode("utf-8", "replace")
            stderr = stderr_bytes.decode("utf-8", "replace")
        except TimeoutError:
            process.kill()
            await process.wait()
            raise BackendError(f"{cmd_str} timed out after {self.timeout_sec}s")

        return _parse_json_result(cmd_str, stdout, stderr, process.returncode or 0)

    async def list_tools(self) -> list[dict[str, Any]]:
        try:
            response = await self._run(["list_tools"])
            raw = (response.get("result") or {}).get("tools")
            return _normalize_tool_definitions(raw)
        except Exception:
            return list(get_tool_definitions())

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self._run([name, "--input-payload", json.dumps(arguments, sort_keys=True)])


class HarborBackend(ToolBackend):
    """Execute tool calls inside a Harbor-managed environment."""

    def __init__(self, environment: Any, *, executable: str = "gmail", timeout_sec: int = 120) -> None:
        self.environment = environment
        self.executable = executable
        self.timeout_sec = timeout_sec

    def describe(self) -> dict[str, Any]:
        return {"backend": "harbor", "command": self.executable}

    async def _run(self, argv: Sequence[str]) -> dict[str, Any]:
        command = shlex.join([self.executable, *argv])
        result = await self.environment.exec(command=command, timeout_sec=self.timeout_sec)
        return _parse_json_result(command, result.stdout, result.stderr, result.return_code)

    async def list_tools(self) -> list[dict[str, Any]]:
        try:
            response = await self._run(["list_tools"])
            raw = (response.get("result") or {}).get("tools")
            return _normalize_tool_definitions(raw)
        except Exception:
            return list(get_tool_definitions())

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self._run([name, "--input-payload", json.dumps(arguments, sort_keys=True)])

