"""End-to-end evaluation tests for terminal incident remediation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from terminal_sim.seed import seed_database
from terminal_sim.service import TerminalService, export_state
from terminal_sim.terminal_reward import evaluate_terminal_episode
from verifiers.layered import evaluate_episode


class TestEndToEnd(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_e2e.db"
        self.conn = seed_database(self.db_path)
        self.svc = TerminalService(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        self.temp_dir.cleanup()

    def test_oracle_flow_scores_perfect_1_0(self) -> None:
        # Step 1: ps aux
        self.svc.execute_tool("run_command", {"command": "ps aux"})

        # Step 2: kill rogue worker
        self.svc.execute_tool("run_command", {"command": "kill -9 4921"})

        # Step 3: truncate bloated debug log
        self.svc.execute_tool("run_command", {"command": "truncate -s 0 /var/log/app/debug_trace.log"})

        # Step 4: repair config
        cfg = self.svc.execute_tool("read_file", {"path": "/etc/payment-processor/config.yaml"})["content"]
        fixed = cfg.replace("db-replica-invalid.internal", "db-primary.internal").replace("9999", "5432")
        self.svc.execute_tool("write_file", {"path": "/etc/payment-processor/config.yaml", "content": fixed})

        # Step 5: secure key permissions
        self.svc.execute_tool("run_command", {"command": "chmod 600 /etc/ssl/certs/payment-api.key"})

        # Step 6: restart service
        self.svc.execute_tool("run_command", {"command": "systemctl restart payment-processor"})

        # Step 7: submit task
        self.svc.execute_tool("submit_task", {
            "summary": "Remediated server degradation",
            "actions_taken": ["killed 4921", "truncated log", "fixed config", "secured key", "restarted service"],
        })

        state = export_state(self.conn)
        eval_res = evaluate_terminal_episode(state)

        self.assertEqual(eval_res["success"], 1.0)
        self.assertEqual(eval_res["valid"], 1.0)
        self.assertEqual(eval_res["reward"], 1.0)
        self.assertEqual(eval_res["audit_pass"], 1.0)
        self.assertEqual(eval_res["audit_findings"], 0)


if __name__ == "__main__":
    unittest.main()
