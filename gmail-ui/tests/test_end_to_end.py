"""End-to-end verification of Oracle, Agent loop (with Ollama provider), and Reward functions."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from agent.backends import InProcessBackend
from agent.loop import ToolLoop
from agent.providers import Completion, OllamaProvider, ToolCall, build_provider
from gmail_sim.seed import seed_database
from gmail_sim.service import execute_tool, export_state
from gmail_sim.sqlite_common import get_connection
from verifiers.layered import evaluate_episode


class TestEndToEnd(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "gmail.db"
        self.snapshot_path = Path(self.temp_dir.name) / "snapshot.sql"
        seed_database(self.db_path, snapshot_path=self.snapshot_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. Oracle Execution Test
    # -------------------------------------------------------------------------
    def test_oracle_execution_and_full_reward(self) -> None:
        """The reference oracle must complete all instructions and score exactly 1.000."""
        # Step 1: Find invoice message and flag it
        inbox_msgs = execute_tool(self.db_path, "list_emails", {"folder": "inbox"})["messages"]
        invoice = next(
            m for m in inbox_msgs
            if "invoice" in (m["subject"] or "").lower() or "billing" in (m["sender"] or "").lower()
        )
        execute_tool(
            self.db_path,
            "update_email",
            {"id": invoice["id"], "isStarred": True, "isImportant": True, "isRead": True},
        )

        # Step 2: Archive shipping notices
        shipping = next(
            m for m in inbox_msgs
            if "shipping" in (m["subject"] or "").lower() or "logistics" in (m["sender"] or "").lower()
        )
        execute_tool(
            self.db_path,
            "update_email",
            {"id": shipping["id"], "isArchived": True},
        )

        # Step 3: Create confirmation draft for finance
        execute_tool(
            self.db_path,
            "create_draft",
            {
                "to": ["finance@corp.co"],
                "subject": "Payment Confirmation Received",
                "body": "Thank you, I have reviewed the invoice and marked it for processing.",
            },
        )

        # Step 4: Submit task report
        execute_tool(
            self.db_path,
            "submit_task",
            {
                "summary": "Completed triage: flagged invoice, archived shipping notice, and created finance confirmation draft.",
                "affected_message_ids": [invoice["id"]],
            },
        )

        # Verify episode reward
        with get_connection(self.db_path) as conn:
            state = export_state(conn)

        evaluation = evaluate_episode(state_data=state)
        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.reward, 1.0)
        self.assertTrue(evaluation.valid)
        self.assertEqual(len(evaluation.penalties), 0)

        # All checks must pass
        for check in evaluation.checks:
            self.assertTrue(check.passed, f"Check {check.name} failed unexpectedly")

    # -------------------------------------------------------------------------
    # 2. Agent with Ollama Provider Test
    # -------------------------------------------------------------------------
    def test_agent_ollama_provider_configuration(self) -> None:
        """Verify Ollama provider instantiation and schema generation."""
        provider = build_provider("ollama/qwen3.6:35b")
        self.assertIsInstance(provider, OllamaProvider)
        self.assertEqual(provider.model, "qwen3.6:35b")
        self.assertEqual(provider.provider_name, "ollama")
        self.assertIn("11434", getattr(provider, "base_url", ""))

    def test_agent_tool_loop_with_ollama(self) -> None:
        """Verify the agent ToolLoop driving an InProcessBackend with an Ollama provider."""
        provider = build_provider("ollama/qwen3.6:35b")
        backend = InProcessBackend(db_path=str(self.db_path))

        # We simulate Ollama's response stream:
        # Turn 1: model decides to call list_emails(folder="inbox")
        # Turn 2: model inspects results and finishes with an answer
        turn1_completion = Completion(
            text="I will check the inbox first.",
            tool_calls=(
                ToolCall(
                    id="call_001",
                    name="list_emails",
                    arguments={"folder": "inbox"},
                ),
            ),
            finish_reason="tool_calls",
            prompt_tokens=150,
            completion_tokens=30,
        )
        turn2_completion = Completion(
            text="I have reviewed the inbox messages.",
            tool_calls=(),
            finish_reason="stop",
            prompt_tokens=350,
            completion_tokens=40,
        )

        call_count = 0

        def mock_complete(messages: Any, **kwargs: Any) -> Completion:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return turn1_completion
            return turn2_completion

        with patch.object(provider, "complete", side_effect=mock_complete):
            loop = ToolLoop(provider, backend, max_turns=5)
            result = asyncio.run(loop.run("Triage unread emails in the inbox."))

            self.assertEqual(result.stop_reason, "finished")
            self.assertEqual(len(result.turns), 2)
            self.assertEqual(call_count, 2)

            # Turn 1 executed the list_emails tool
            first_turn = result.turns[0]
            self.assertEqual(len(first_turn.tool_calls), 1)
            self.assertEqual(first_turn.tool_calls[0].name, "list_emails")
            self.assertEqual(len(first_turn.results), 1)
            self.assertTrue(first_turn.results[0]["ok"])
            self.assertIn("messages", first_turn.results[0]["result"])

    # -------------------------------------------------------------------------
    # 3. Reward Functions: Positive and Negative Cases
    # -------------------------------------------------------------------------
    def test_reward_positive_permuted_order(self) -> None:
        """Positive Case: Alternate order of operations still earns 100% reward."""
        # 1. Draft created first
        execute_tool(
            self.db_path,
            "create_draft",
            {
                "to": ["finance@corp.co"],
                "subject": "Payment Confirmation Received",
                "body": "Invoice reviewed and queued.",
            },
        )
        # 2. Shipping archived
        execute_tool(self.db_path, "update_email", {"id": "MSG_SHIP_002", "isArchived": True})
        # 3. Invoice flagged
        execute_tool(
            self.db_path,
            "update_email",
            {"id": "MSG_INV_001", "isStarred": True, "isImportant": True, "isRead": True},
        )

        with get_connection(self.db_path) as conn:
            state = export_state(conn)

        evaluation = evaluate_episode(state_data=state)
        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.reward, 1.0)
        self.assertTrue(evaluation.valid)

    def test_reward_negative_missing_draft(self) -> None:
        """Negative Case 1: Flagged invoice and archived notice, but forgot draft."""
        execute_tool(
            self.db_path,
            "update_email",
            {"id": "MSG_INV_001", "isStarred": True, "isImportant": True, "isRead": True},
        )
        execute_tool(self.db_path, "update_email", {"id": "MSG_SHIP_002", "isArchived": True})

        with get_connection(self.db_path) as conn:
            state = export_state(conn)

        evaluation = evaluate_episode(state_data=state)
        self.assertFalse(evaluation.passed)
        self.assertLess(evaluation.reward, 1.0)

        checks_by_name = {c.name: c for c in evaluation.checks}
        self.assertTrue(checks_by_name["finance_email_flagged"].passed)
        self.assertTrue(checks_by_name["notice_email_archived"].passed)
        self.assertFalse(checks_by_name["confirmation_draft_created"].passed)

    def test_reward_negative_wrong_recipient_in_draft(self) -> None:
        """Negative Case 2: Draft created, but addressed to the wrong recipient."""
        execute_tool(
            self.db_path,
            "update_email",
            {"id": "MSG_INV_001", "isStarred": True, "isImportant": True, "isRead": True},
        )
        execute_tool(self.db_path, "update_email", {"id": "MSG_SHIP_002", "isArchived": True})
        # Wrong recipient: colleague instead of finance@corp.co
        execute_tool(
            self.db_path,
            "create_draft",
            {
                "to": ["colleague@company.com"],
                "subject": "Payment Confirmation Received",
                "body": "Invoice reviewed.",
            },
        )

        with get_connection(self.db_path) as conn:
            state = export_state(conn)

        evaluation = evaluate_episode(state_data=state)
        self.assertFalse(evaluation.passed)
        checks_by_name = {c.name: c for c in evaluation.checks}
        self.assertFalse(checks_by_name["confirmation_draft_created"].passed)

    def test_reward_negative_cleanliness_violation(self) -> None:
        """Negative Case 3: Trashing emails violates scope cleanliness."""
        # Complete all steps...
        execute_tool(
            self.db_path,
            "update_email",
            {"id": "MSG_INV_001", "isStarred": True, "isImportant": True, "isRead": True},
        )
        execute_tool(self.db_path, "update_email", {"id": "MSG_SHIP_002", "isArchived": True})
        execute_tool(
            self.db_path,
            "create_draft",
            {"to": ["finance@corp.co"], "subject": "Payment Confirmation Received", "body": "Ok"},
        )
        # ...but also indiscriminately trash emails
        execute_tool(self.db_path, "update_email", {"id": "MSG_PROJ_003", "isTrash": True})

        with get_connection(self.db_path) as conn:
            state = export_state(conn)

        evaluation = evaluate_episode(state_data=state)
        self.assertFalse(evaluation.passed)
        self.assertLess(evaluation.reward, 1.0)

        checks_by_name = {c.name: c for c in evaluation.checks}
        self.assertFalse(checks_by_name["scope_cleanliness"].passed)

    def test_reward_negative_noop_episode(self) -> None:
        """Negative Case 4: No actions taken at all produces a failing evaluation."""
        with get_connection(self.db_path) as conn:
            state = export_state(conn)

        evaluation = evaluate_episode(state_data=state)
        self.assertFalse(evaluation.passed)
        checks_by_name = {c.name: c for c in evaluation.checks}
        self.assertFalse(checks_by_name["finance_email_flagged"].passed)
        self.assertFalse(checks_by_name["confirmation_draft_created"].passed)


if __name__ == "__main__":
    unittest.main()
