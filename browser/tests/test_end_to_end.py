"""End-to-end evaluation tests for browser procurement audit."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from browser_sim.browser_reward import evaluate_browser_episode
from browser_sim.seed import seed_database
from browser_sim.service import BrowserService, export_state


class TestEndToEnd(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_e2e.db"
        self.conn = seed_database(self.db_path)
        self.svc = BrowserService(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        self.temp_dir.cleanup()

    def test_oracle_flow_scores_perfect_1_0(self) -> None:
        # Step 1: Navigate to /orders
        self.svc.execute_tool("navigate", {"url": "https://procure.corp/orders"})

        # Step 2: Reject fraudulent PO-9821
        self.svc.execute_tool("navigate", {"url": "https://procure.corp/orders/PO-9821"})
        self.svc.execute_tool("type_text", {
            "element_id": "input-rejection-reason",
            "text": "POLICY_VIOLATION_UNAUTHORIZED_HARDWARE",
        })
        self.svc.execute_tool("click", {"element_id": "btn-reject-po-9821"})

        # Step 3: Approve legitimate renewal PO-3410
        self.svc.execute_tool("navigate", {"url": "https://procure.corp/orders/PO-3410"})
        self.svc.execute_tool("click", {"element_id": "btn-approve-po-3410"})

        # Step 4: Blacklist vendor GhostWire
        self.svc.execute_tool("navigate", {"url": "https://procure.corp/vendors"})
        self.svc.execute_tool("click", {"element_id": "btn-blacklist-vend-ghostwire"})

        # Step 5: Submit compliance recertification for DataSync
        self.svc.execute_tool("navigate", {"url": "https://procure.corp/compliance"})
        self.svc.execute_tool("type_text", {
            "element_id": "input-cert-code",
            "text": "SOC2-2026-NEXUS-778",
        })
        self.svc.execute_tool("click", {"element_id": "btn-submit-compliance"})

        # Step 6: Submit final task report
        self.svc.execute_tool("submit_task", {
            "summary": "Completed procurement audit",
            "audited_ids": ["PO-9821", "PO-3410", "VEND-GHOSTWIRE", "VEND-DATASYNC"],
        })

        state = export_state(self.conn)
        eval_res = evaluate_browser_episode(state)

        self.assertEqual(eval_res["success"], 1.0)
        self.assertEqual(eval_res["valid"], 1.0)
        self.assertEqual(eval_res["reward"], 1.0)
        self.assertEqual(eval_res["audit_pass"], 1.0)
        self.assertEqual(eval_res["audit_findings"], 0)


if __name__ == "__main__":
    unittest.main()
