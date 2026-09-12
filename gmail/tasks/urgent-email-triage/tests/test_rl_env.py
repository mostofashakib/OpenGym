"""Tests for the Gmail RL Environment contract and CLI interface."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gmail_sim.environment import GmailEnvironment


class TestGmailRLEnvironment(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "gmail.db"
        self.snapshot_path = Path(self.temp_dir.name) / "snapshot.sql"
        self.env = GmailEnvironment(db_path=self.db_path, snapshot_path=self.snapshot_path)
        self.env.setup_state(seed=42)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_setup_and_prompts(self) -> None:
        setup_res = self.env.setup()
        self.assertTrue(setup_res["persistent"])
        self.assertGreaterEqual(setup_res["tool_count"], 10)

        prompts = self.env.prompts()
        self.assertGreaterEqual(len(prompts), 1)
        self.assertEqual(prompts[0]["id"], "gmail_assistant")

        rendered = self.env.render_prompt("gmail_assistant", instruction="Triage inbox.")
        self.assertIn("Gmail Assistant Operator", rendered)
        self.assertIn("Triage inbox.", rendered)

    def test_reset_and_step_cycle(self) -> None:
        session = self.env.reset(
            session_cookie="sess_test_1",
            seed=42,
            user_instruction="Find invoice email",
        )
        self.assertEqual(session["session_cookie"], "sess_test_1")
        self.assertEqual(session["turn"], 0)

        # Step 1: search emails
        step_1 = self.env.step(
            session_cookie="sess_test_1",
            tool_name="search_emails",
            input_payload={"query": "from:billing@company.com"},
        )
        self.assertEqual(step_1["turn"], 1)
        self.assertTrue(step_1["observation"]["ok"])
        messages = step_1["observation"]["result"]["messages"]
        self.assertGreater(len(messages), 0)
        inv_id = messages[0]["id"]

        # Step 2: update email
        step_2 = self.env.step(
            session_cookie="sess_test_1",
            tool_name="update_email",
            input_payload={"id": inv_id, "isStarred": True, "isRead": True},
        )
        self.assertEqual(step_2["turn"], 2)
        self.assertTrue(step_2["observation"]["ok"])

        # Inspect state & history
        state = self.env.state("sess_test_1")
        self.assertEqual(state["turns_taken"], 2)

        hist = self.env.history("sess_test_1")
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0]["tool_name"], "search_emails")
        self.assertEqual(hist[1]["tool_name"], "update_email")


if __name__ == "__main__":
    unittest.main()
