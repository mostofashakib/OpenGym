"""Unit tests for terminal_sim package."""

from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from terminal_sim.seed import seed_database
from terminal_sim.service import TerminalService, export_state
from terminal_sim.sqlite_common import init_db


class TestTerminalSim(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_terminal.db"
        self.conn = seed_database(self.db_path)
        self.svc = TerminalService(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        self.temp_dir.cleanup()

    def test_seed_contents(self) -> None:
        state = export_state(self.conn)
        self.assertTrue(len(state["files"]) >= 10)
        self.assertTrue(len(state["processes"]) >= 5)
        self.assertTrue(len(state["services"]) >= 4)
        self.assertEqual(state["system_metrics"]["disk_total_mb"], 20480)

    def test_ps_and_kill(self) -> None:
        ps_res = self.svc.execute_tool("run_command", {"command": "ps aux"})
        self.assertIn("4921", ps_res["stdout"])
        self.assertIn("worker-leak.py", ps_res["stdout"])

        kill_res = self.svc.execute_tool("run_command", {"command": "kill -9 4921"})
        self.assertEqual(kill_res["exit_code"], 0)

        ps_after = self.svc.execute_tool("run_command", {"command": "ps aux"})
        self.assertNotIn("4921", ps_after["stdout"])

    def test_df_and_log_truncation(self) -> None:
        df_res = self.svc.execute_tool("run_command", {"command": "df -h"})
        self.assertIn("/dev/sda1", df_res["stdout"])
        self.assertIn("96%", df_res["stdout"])

        # Truncate debug log
        trunc_res = self.svc.execute_tool(
            "run_command", {"command": "truncate -s 0 /var/log/app/debug_trace.log"}
        )
        self.assertEqual(trunc_res["exit_code"], 0)

        df_after = self.svc.execute_tool("run_command", {"command": "df -h"})
        self.assertIn("4%", df_after["stdout"])

    def test_chmod(self) -> None:
        chmod_res = self.svc.execute_tool(
            "run_command", {"command": "chmod 600 /etc/ssl/certs/payment-api.key"}
        )
        self.assertEqual(chmod_res["exit_code"], 0)

        read_res = self.svc.execute_tool(
            "read_file", {"path": "/etc/ssl/certs/payment-api.key"}
        )
        self.assertEqual(read_res["permissions"], "600")

    def test_systemctl_lifecycle(self) -> None:
        # Initially failed
        status_res = self.svc.execute_tool("run_command", {"command": "systemctl status payment-processor"})
        self.assertIn("Active: failed", status_res["stdout"])

        # Restarting before config fix fails
        restart_fail = self.svc.execute_tool("run_command", {"command": "systemctl restart payment-processor"})
        self.assertEqual(restart_fail["exit_code"], 1)

        # Fix config and permissions
        cfg = self.svc.execute_tool("read_file", {"path": "/etc/payment-processor/config.yaml"})["content"]
        fixed = cfg.replace("db-replica-invalid.internal", "db-primary.internal").replace("9999", "5432")
        self.svc.execute_tool("write_file", {"path": "/etc/payment-processor/config.yaml", "content": fixed})
        self.svc.execute_tool("run_command", {"command": "chmod 600 /etc/ssl/certs/payment-api.key"})

        # Restarting now succeeds
        restart_ok = self.svc.execute_tool("run_command", {"command": "systemctl restart payment-processor"})
        self.assertEqual(restart_ok["exit_code"], 0)

        status_ok = self.svc.execute_tool("run_command", {"command": "systemctl status payment-processor"})
        self.assertIn("Active: active (running)", status_ok["stdout"])


if __name__ == "__main__":
    unittest.main()
