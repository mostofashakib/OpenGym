"""Test browser bridge for browser-ui."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIDGE_SCRIPT = ROOT / "scripts" / "browser_bridge.py"


class TestBrowserBridge(unittest.TestCase):
    def test_get_dashboard(self):
        cmd = [sys.executable, str(BRIDGE_SCRIPT), "get_dashboard"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertIn("orders", data)
        self.assertIn("vendors", data)
        self.assertIn("stats", data)
        self.assertEqual(data["stats"]["pending_orders"], 2)

    def test_call_tool_via_bridge(self):
        cmd = [
            sys.executable,
            str(BRIDGE_SCRIPT),
            "call_tool",
            "navigate",
            json.dumps({"url": "https://procure.corp/orders"}),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertTrue(data.get("success", False))
        self.assertIn("Purchase Orders", data.get("page", {}).get("title", ""))

    def test_export_state_via_bridge(self):
        cmd = [sys.executable, str(BRIDGE_SCRIPT), "export_state"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertIn("orders", data)
        self.assertIn("vendors", data)


if __name__ == "__main__":
    unittest.main()
