"""Test slack bridge for slack-ui."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

ENV = {**os.environ, "PYTHONPATH": f"environment:{os.environ.get('PYTHONPATH', '')}"}


class TestSlackBridge(unittest.TestCase):
    def test_list_channels(self):
        cmd = [sys.executable, "-m", "scripts.slack_bridge", "list_channels"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
        data = json.loads(res.stdout)
        self.assertIn("channels", data)
        names = [c["name"] for c in data["channels"]]
        self.assertIn("acme-migration", names)
        self.assertIn("debugging", names)

    def test_get_messages(self):
        cmd = [sys.executable, "-m", "scripts.slack_bridge", "get_messages", "C019"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
        data = json.loads(res.stdout)
        self.assertIn("messages", data)
        self.assertTrue(len(data["messages"]) > 0)
        # Check Daniel Cho's prompt
        prompt_msg = next((m for m in data["messages"] if m["id"] == "MSG145"), None)
        self.assertIsNotNone(prompt_msg)
        self.assertEqual(prompt_msg["author_handle"], "daniel")

    def test_call_tool_via_bridge(self):
        cmd = [
            sys.executable,
            "-m",
            "scripts.slack_bridge",
            "call_tool",
            "list_users",
            json.dumps({"limit": 10}),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, env=ENV)
        data = json.loads(res.stdout)
        self.assertIn("users", data)


if __name__ == "__main__":
    unittest.main()
