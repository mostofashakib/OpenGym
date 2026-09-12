"""State checks for Gmail environment verification."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from verifiers.results import CheckOutcome


def _load_state(client: Any | None = None, state_data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if state_data is not None:
        return state_data

    # 1. Try sockets (admin.sock or agent.sock in shared volume /run/gmail)
    for sock in [
        os.environ.get("GMAIL_ADMIN_SOCKET", "/run/gmail/admin.sock"),
        os.environ.get("GMAIL_SOCKET", "/run/gmail/agent.sock"),
    ]:
        if os.path.exists(sock):
            try:
                from gmail_sim.protocol import request
                resp = request(sock, {"op": "export_state", "tool": "export_state"})
                if resp.get("ok") and "result" in resp:
                    return resp["result"]
            except Exception:
                pass

    # 2. Try state export artifact (written by verifier.collect or admin_cli)
    for candidate in [
        Path("/var/lib/gmail/state-export.json"),
        Path("/tmp/state-export.json"),
        Path("state-export.json"),
    ]:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                pass

    # 2. Try direct SQLite database
    for db_candidate in [
        Path("/var/lib/gmail/gmail.db"),
        Path("/tmp/test_gmail.db"),
    ]:
        if db_candidate.exists():
            try:
                from gmail_sim.service import export_state
                from gmail_sim.sqlite_common import get_connection

                with get_connection(db_candidate) as conn:
                    return export_state(conn)
            except Exception:
                pass

    # 3. Try HTTP client if available
    if client is not None:
        try:
            res = client.get_state()
            if res.get("ok"):
                return res.get("result", {})
        except Exception:
            pass

    return None


def evaluate_triage_task(
    client: Any | None = None,
    state_data: dict[str, Any] | None = None,
) -> list[CheckOutcome]:
    """Evaluate whether the requested email triage operations were performed."""
    state = _load_state(client, state_data)
    if state is None:
        return [
            CheckOutcome(
                name="state_fetchable",
                passed=False,
                detail={"error": "Could not retrieve state from client, export file, or database"},
                weight=1.0,
            )
        ]

    messages = state.get("messages", [])
    drafts_list = state.get("drafts", [])
    if not drafts_list and client is not None:
        try:
            drafts_res = client.tool_list_drafts()
            drafts_list = drafts_res.get("result", {}).get("drafts", [])
        except Exception:
            pass
    if not drafts_list:
        drafts_list = [m for m in messages if "DRAFTS" in (m.get("labelIds") or [])]

    # Check 1: Finance / Billing email is starred, important, and read
    finance_msgs = [
        m for m in messages
        if "billing@company.com" in (m.get("sender") or "").lower()
        or "finance@corp.co" in (m.get("sender") or "").lower()
        or "invoice" in (m.get("subject") or "").lower()
    ]

    starred_and_read = False
    if finance_msgs:
        starred_and_read = any(
            m.get("isStarred") and m.get("isImportant") and m.get("isRead")
            for m in finance_msgs
        )

    checks = [
        CheckOutcome(
            name="finance_email_flagged",
            passed=starred_and_read,
            detail={
                "found_candidates": len(finance_msgs),
                "matched": starred_and_read,
            },
            weight=1.0,
        )
    ]

    # Check 2: Notice/notification email archived
    notice_msgs = [
        m for m in messages
        if "shipping" in (m.get("subject") or "").lower()
        or "notice" in (m.get("subject") or "").lower()
        or "order confirmation" in (m.get("subject") or "").lower()
    ]

    archived_ok = False
    if notice_msgs:
        archived_ok = any(
            m.get("isArchived")
            or "ARCHIVE" in (m.get("labelIds") or [])
            or "INBOX" not in (m.get("labelIds") or [])
            for m in notice_msgs
        )

    checks.append(
        CheckOutcome(
            name="notice_email_archived",
            passed=archived_ok,
            detail={
                "found_candidates": len(notice_msgs),
                "archived": archived_ok,
            },
            weight=1.0,
        )
    )

    # Check 3: Draft created for finance confirmation
    draft_ok = any(
        any("finance@corp.co" in addr.lower() for addr in d.get("to", []))
        and "payment confirmation" in (d.get("subject") or "").lower()
        for d in drafts_list
    )

    checks.append(
        CheckOutcome(
            name="confirmation_draft_created",
            passed=draft_ok,
            detail={"drafts_count": len(drafts_list), "matched": draft_ok},
            weight=1.0,
        )
    )

    # Check 4: Cleanliness - No unintended deletions
    trashed = [m for m in messages if m.get("isTrash")]
    clean_trash = len(trashed) == 0

    checks.append(
        CheckOutcome(
            name="scope_cleanliness",
            passed=clean_trash,
            detail={"trashed_count": len(trashed)},
            weight=0.5,
        )
    )

    return checks
