"""Test task bridge for task_manager-ui."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIDGE_SCRIPT = ROOT / "scripts" / "task_bridge.py"


class TestTaskBridge(unittest.TestCase):
    def test_list_projects(self):
        cmd = [sys.executable, str(BRIDGE_SCRIPT), "list_projects"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertIn("projects", data)
        names = [p["name"] for p in data["projects"]]
        self.assertIn("Titanium Enterprise v3.0", names)

    def test_list_tasks(self):
        cmd = [
            sys.executable,
            str(BRIDGE_SCRIPT),
            "list_tasks",
            json.dumps({"project_id": "P005"}),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertIn("tasks", data)
        self.assertTrue(len(data["tasks"]) > 0)
        task_ids = [t["task_id"] for t in data["tasks"]]
        self.assertIn("TASK037", task_ids)

    def test_call_tool_via_bridge(self):
        cmd = [
            sys.executable,
            str(BRIDGE_SCRIPT),
            "call_tool",
            "get_task",
            json.dumps({"task_id": "TASK037"}),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("task", {}).get("task_id"), "TASK037")


if __name__ == "__main__":
    unittest.main()
