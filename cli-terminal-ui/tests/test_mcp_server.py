"""Tests for terminal MCP server."""

from __future__ import annotations

import json
import unittest

from terminal_sim.mcp_server import dispatch, tool_list


class TestMCPServer(unittest.TestCase):
    def test_tool_list(self) -> None:
        tools = tool_list()
        names = {t["name"] for t in tools}
        self.assertIn("run_command", names)
        self.assertIn("read_file", names)
        self.assertIn("write_file", names)
        self.assertIn("list_processes", names)
        self.assertIn("inspect_system", names)
        self.assertIn("submit_task", names)

    def test_initialize(self) -> None:
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}
        res = dispatch(req)
        self.assertIsNotNone(res)
        self.assertEqual(res["result"]["serverInfo"]["name"], "terminal")

    def test_tools_list_dispatch(self) -> None:
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        res = dispatch(req)
        self.assertIsNotNone(res)
        self.assertTrue(len(res["result"]["tools"]) >= 5)


if __name__ == "__main__":
    unittest.main()
