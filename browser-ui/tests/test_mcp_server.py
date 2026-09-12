"""Tests for browser MCP server."""

from __future__ import annotations

import unittest
from browser_sim.mcp_server import dispatch, tool_list


class TestMCPServer(unittest.TestCase):
    def test_tool_list(self) -> None:
        tools = tool_list()
        names = {t["name"] for t in tools}
        self.assertIn("navigate", names)
        self.assertIn("get_page", names)
        self.assertIn("click", names)
        self.assertIn("type_text", names)
        self.assertIn("select_option", names)
        self.assertIn("submit_form", names)
        self.assertIn("go_back", names)
        self.assertIn("submit_task", names)

    def test_initialize(self) -> None:
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}
        res = dispatch(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["result"]["serverInfo"]["name"], "browser")

    def test_tools_list_dispatch(self) -> None:
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = dispatch(req)
        self.assertIsNotNone(res)
        self.assertTrue(len(res["result"]["tools"]) >= 6)


if __name__ == "__main__":
    unittest.main()
