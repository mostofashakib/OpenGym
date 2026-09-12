"""Unit tests for browser_sim package."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from browser_sim.seed import seed_database
from browser_sim.service import BrowserService, export_state


class TestBrowserSim(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_browser.db"
        self.conn = seed_database(self.db_path)
        self.svc = BrowserService(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        self.temp_dir.cleanup()

    def test_seed_contents(self) -> None:
        state = export_state(self.conn)
        self.assertEqual(len(state["orders"]), 4)
        self.assertEqual(len(state["vendors"]), 4)
        self.assertEqual(state["browser_session"]["current_url"], "https://procure.corp/dashboard")

    def test_navigation_and_rendering(self) -> None:
        nav_res = self.svc.execute_tool("navigate", {"url": "/orders"})
        self.assertEqual(nav_res["url"], "https://procure.corp/orders")
        page = nav_res["page"]
        self.assertIn("PO-9821", page["content"])
        self.assertIn("PO-3410", page["content"])
        self.assertTrue(any(el["id"] == "btn-reject-po-9821" for el in page["interactive_elements"]))

    def test_reject_fraud_order(self) -> None:
        self.svc.execute_tool("navigate", {"url": "/orders/PO-9821"})
        self.svc.execute_tool("type_text", {
            "element_id": "input-rejection-reason",
            "text": "POLICY_VIOLATION_UNAUTHORIZED_HARDWARE",
        })
        rej_res = self.svc.execute_tool("click", {"element_id": "btn-reject-po-9821"})
        self.assertEqual(rej_res["status"], "REJECTED")

        # Verify in DB
        row = self.conn.execute("SELECT * FROM orders WHERE id = 'PO-9821'").fetchone()
        self.assertEqual(row["status"], "REJECTED")
        self.assertEqual(row["rejection_reason"], "POLICY_VIOLATION_UNAUTHORIZED_HARDWARE")

    def test_approve_renewal(self) -> None:
        self.svc.execute_tool("navigate", {"url": "/orders/PO-3410"})
        app_res = self.svc.execute_tool("click", {"element_id": "btn-approve-po-3410"})
        self.assertEqual(app_res["status"], "APPROVED")

        row = self.conn.execute("SELECT * FROM orders WHERE id = 'PO-3410'").fetchone()
        self.assertEqual(row["status"], "APPROVED")

    def test_blacklist_vendor(self) -> None:
        self.svc.execute_tool("navigate", {"url": "/vendors"})
        bl_res = self.svc.execute_tool("click", {"element_id": "btn-blacklist-vend-ghostwire"})
        self.assertEqual(bl_res["status"], "BLACKLISTED")

        row = self.conn.execute("SELECT * FROM vendors WHERE id = 'VEND-GHOSTWIRE'").fetchone()
        self.assertEqual(row["status"], "BLACKLISTED")

    def test_compliance_renewal(self) -> None:
        self.svc.execute_tool("navigate", {"url": "/compliance"})
        self.svc.execute_tool("type_text", {
            "element_id": "input-cert-code",
            "text": "SOC2-2026-NEXUS-778",
        })
        sub_res = self.svc.execute_tool("click", {"element_id": "btn-submit-compliance"})
        self.assertIn("SOC2-2026-NEXUS-778", sub_res["cert_reference"])

        row = self.conn.execute("SELECT * FROM vendors WHERE id = 'VEND-DATASYNC'").fetchone()
        self.assertEqual(row["soc2_certified"], 1)


if __name__ == "__main__":
    unittest.main()
