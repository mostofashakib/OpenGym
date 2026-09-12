"""Tests for Gmail MCP server."""

from __future__ import annotations

import json
from typing import Any
import unittest

from tools.gmail_client import GmailClient
from tools.mcp_server import dispatch


class DummyGmailClient(GmailClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://127.0.0.1:9999")

    def execute_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        actual_args = arguments if arguments is not None else (args or {})
        return {"ok": True, "result": {"echo_tool": name, "args": actual_args}}


class TestMcpServer(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DummyGmailClient()

    def test_initialize(self) -> None:
        msg = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}
        res = dispatch(msg, self.client)
        assert res is not None
        self.assertIsNotNone(res)
        self.assertEqual(res["result"]["serverInfo"]["name"], "gmail")

    def test_tools_list(self) -> None:
        msg = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        res = dispatch(msg, self.client)
        assert res is not None
        self.assertIsNotNone(res)
        tools = res["result"]["tools"]
        names = [t["name"] for t in tools]
        self.assertIn("list_emails", names)
        self.assertIn("send_email", names)
        self.assertIn("update_email", names)
        self.assertIn("submit_task", names)

    def test_tools_call(self) -> None:
        msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_emails",
                "arguments": {"folder": "inbox"},
            },
        }
        res = dispatch(msg, self.client)
        assert res is not None
        self.assertIsNotNone(res)
        content = res["result"]["content"]
        self.assertTrue(len(content) > 0)
        parsed = json.loads(content[0]["text"])
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["result"]["echo_tool"], "list_emails")


if __name__ == "__main__":
    unittest.main()
