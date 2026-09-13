"""Tests for the layered verifier, predicate breakdown, and audit penalties."""

from __future__ import annotations

import tempfile
from pathlib import Path

from solution.oracle import solve
from tools.workstation_client import WorkstationClient
from verifiers.layered import evaluate_episode
from workstation_sim.seed import seed_database


def test_verifier_untouched_state_scores_zero() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        client = WorkstationClient(db_path=db)

        eval_res = evaluate_episode(client)
        assert eval_res.reward == 0.0
        assert eval_res.passed is False
        assert len(eval_res.checks) == 7
        assert all(c.passed is False for c in eval_res.checks)


def test_verifier_oracle_scores_perfect() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        client = WorkstationClient(db_path=db)

        solve(client)

        eval_res = evaluate_episode(client)
        assert eval_res.reward == 1.0, f"Expected 1.0 reward for oracle, got {eval_res.reward}"
        assert eval_res.passed is True
        assert len(eval_res.penalties) == 0
        assert all(c.passed is True for c in eval_res.checks)


def test_verifier_privacy_audit_penalty_applied() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        client = WorkstationClient(db_path=db)

        # Execute oracle
        solve(client)

        # Now simulate snooping into an unrelated customer record (e.g. CUST-1002 Globex Corp)
        client.get_customer("CUST-1002")

        eval_res = evaluate_episode(client)
        assert eval_res.passed is False, "Run with privacy violations must not pass audit"
        assert any("Privacy violation" in p.reason for p in eval_res.penalties)
        assert eval_res.reward < 1.0, f"Expected penalty deduction, got reward {eval_res.reward}"


def test_verifier_causal_order_penalty_applied() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        client = WorkstationClient(db_path=db)

        # Send confirmation email FIRST (before issuing refund)
        client.send_email(
            to=["sarah.jenkins@acme.com"],
            subject="Refund Confirmation",
            body="We have refunded $9,024.66.",
        )

        # Issue refund afterwards
        client.issue_refund("INV-3817", 902466, "Cancellation")
        client.update_customer("CUST-1042", status="churned")
        client.add_crm_activity("CUST-1042", "note", "cancellation completed")
        client.update_ticket("TICK-2042", status="resolved")
        client.create_event("Acme Debrief", "2026-10-17T10:00:00Z", "2026-10-17T10:30:00Z")

        eval_res = evaluate_episode(client)
        assert any("Procedural order violation" in p.reason for p in eval_res.penalties)
