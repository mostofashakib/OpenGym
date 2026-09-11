"""Tests for the authoritative Gmail simulation service."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from gmail_sim.seed import seed_database
from gmail_sim.service import execute_tool, export_state
from gmail_sim.sqlite_common import get_connection


class TestGmailSim(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_gmail.db"
        self.snapshot_path = Path(self.temp_dir.name) / "snapshot.sql"
        seed_database(self.db_path, snapshot_path=self.snapshot_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_list_and_get_email(self) -> None:
        res = execute_tool(self.db_path, "list_emails", {"folder": "inbox"})
        messages = res["messages"]
        self.assertGreater(len(messages), 0)

        first_id = messages[0]["id"]
        single = execute_tool(self.db_path, "get_email", {"id": first_id})
        self.assertEqual(single["message"]["id"], first_id)

    def test_send_and_reply_email(self) -> None:
        send_res = execute_tool(
            self.db_path,
            "send_email",
            {"to": "colleague@example.com", "subject": "Quarterly Review", "body": "Notes attached."},
        )
        self.assertEqual(send_res["status"], "sent")
        thread_id = send_res["threadId"]

        reply_res = execute_tool(
            self.db_path,
            "reply_thread",
            {"thread_id": thread_id, "body": "Following up on this."},
        )
        self.assertEqual(reply_res["status"], "sent")

        thread_data = execute_tool(self.db_path, "get_thread", {"id": thread_id})
        self.assertEqual(len(thread_data["thread"]["messages"]), 2)

    def test_draft_lifecycle(self) -> None:
        create_res = execute_tool(
            self.db_path,
            "create_draft",
            {"to": "test@example.com", "subject": "Draft Subject", "body": "Draft body"},
        )
        draft_id = create_res["draft"]["id"]

        drafts = execute_tool(self.db_path, "list_drafts", {})["drafts"]
        self.assertTrue(any(d["id"] == draft_id for d in drafts))

        execute_tool(
            self.db_path,
            "update_draft",
            {"id": draft_id, "body": "Updated draft content"},
        )

        sent_res = execute_tool(self.db_path, "send_draft", {"id": draft_id})
        self.assertEqual(sent_res["status"], "sent")

        drafts_after = execute_tool(self.db_path, "list_drafts", {})["drafts"]
        self.assertFalse(any(d["id"] == draft_id for d in drafts_after))

    def test_labels_and_counters(self) -> None:
        label_res = execute_tool(self.db_path, "create_label", {"name": "Finance", "color": "#00FF00"})
        self.assertEqual(label_res["label"]["name"], "Finance")

        labels = execute_tool(self.db_path, "list_labels", {})["labels"]
        self.assertTrue(any(l["name"] == "Finance" for l in labels))

        counters = execute_tool(self.db_path, "get_counters", {})
        self.assertIn("totalInbox", counters)
        self.assertIn("unread", counters)

    def test_export_state(self) -> None:
        with get_connection(self.db_path) as conn:
            state = export_state(conn)
        self.assertIn("messages", state)
        self.assertIn("threads", state)
        self.assertIn("labels", state)
        self.assertIn("action_log", state)


if __name__ == "__main__":
    unittest.main()
