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

    def test_search_emails_operators(self) -> None:
        # Search from:
        res = execute_tool(self.db_path, "search_emails", {"query": "from:billing@company.com"})
        msgs = res["messages"]
        self.assertGreater(len(msgs), 0)
        self.assertTrue(all("billing@company.com" in m["from"] for m in msgs))

        # Search is:unread
        unread_res = execute_tool(self.db_path, "search_emails", {"query": "is:unread"})
        self.assertTrue(all(not m["isRead"] for m in unread_res["messages"]))

        # Search subject:
        sub_res = execute_tool(self.db_path, "search_emails", {"query": "subject:invoice"})
        self.assertGreater(len(sub_res["messages"]), 0)

        # Search OR
        or_res = execute_tool(self.db_path, "search_emails", {"query": "from:billing@company.com OR from:shipping@logistics.net"})
        senders = {m["from"] for m in or_res["messages"]}
        self.assertIn("billing@company.com", senders)
        self.assertIn("shipping@logistics.net", senders)

        # Search with q instead of query
        q_res = execute_tool(self.db_path, "search_emails", {"q": "from:billing@company.com"})
        self.assertGreater(len(q_res["messages"]), 0)

    def test_flexible_arguments_and_aliases(self) -> None:
        # Get by email_id
        inbox_res = execute_tool(self.db_path, "list_emails", {"folder": "inbox"})
        first_id = inbox_res["messages"][0]["id"]
        msg_by_alias = execute_tool(self.db_path, "get_email", {"email_id": first_id})
        self.assertEqual(msg_by_alias["id"], first_id)

        # Update with snake_case
        update_res = execute_tool(
            self.db_path,
            "update_email",
            {"email_id": first_id, "is_starred": True, "is_important": True, "is_read": True},
        )
        self.assertTrue(update_res["message"]["isStarred"])
        self.assertTrue(update_res["message"]["is_starred"])
        self.assertTrue(update_res["message"]["isImportant"])
        self.assertTrue(update_res["message"]["is_important"])
        self.assertTrue(update_res["message"]["isRead"])
        self.assertTrue(update_res["message"]["is_read"])

    def test_list_threads_filtering(self) -> None:
        # Filter by folder
        inbox_threads = execute_tool(self.db_path, "list_threads", {"folder": "inbox"})["threads"]
        self.assertGreater(len(inbox_threads), 0)

        # Filter by query
        invoice_threads = execute_tool(self.db_path, "list_threads", {"q": "invoice"})["threads"]
        self.assertGreater(len(invoice_threads), 0)
        self.assertTrue(any("invoice" in t["subject"].lower() for t in invoice_threads))

    def test_export_state(self) -> None:
        with get_connection(self.db_path) as conn:
            state = export_state(conn)
        self.assertIn("messages", state)
        self.assertIn("threads", state)
        self.assertIn("labels", state)
        self.assertIn("action_log", state)


if __name__ == "__main__":
    unittest.main()
