"""Test terminal bridge for cli-terminal-ui."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIDGE_SCRIPT = ROOT / "scripts" / "terminal_bridge.py"


class TestTerminalBridge(unittest.TestCase):
    def test_get_system(self):
        cmd = [sys.executable, str(BRIDGE_SCRIPT), "get_system"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertIn("system", data)
        self.assertIn("processes", data)
        self.assertIn("services", data)
        self.assertEqual(data["system"]["hostname"], "app-node-04.prod.corp")

    def test_run_command_via_bridge(self):
        cmd = [
            sys.executable,
            str(BRIDGE_SCRIPT),
            "call_tool",
            "run_command",
            json.dumps({"command": "ps aux"}),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data["exit_code"], 0)
        self.assertIn("USER", data["stdout"])

    def test_list_files_via_bridge(self):
        cmd = [sys.executable, str(BRIDGE_SCRIPT), "list_files"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertTrue(isinstance(data, list))
        paths = [f["path"] for f in data]
        self.assertIn("/etc/payment-processor/config.yaml", paths)


if __name__ == "__main__":
    unittest.main()
