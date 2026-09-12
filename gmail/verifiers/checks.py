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


def evaluate_compromise_triage_task(
    client: Any | None = None,
    state_data: dict[str, Any] | None = None,
) -> list[CheckOutcome]:
    """Evaluate whether the incident compromise triage operations were performed."""
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

    # Check 1: Critical vendor breach disclosure flagged, starred, important, and read
    breach_msgs = [
        m for m in messages
        if "datapipe" in (m.get("sender") or "").lower()
        or "KEY_PROD_SEC_8821" in (m.get("snippet") or "")
        or "security advisory" in (m.get("subject") or "").lower()
    ]
    breach_flagged = False
    if breach_msgs:
        breach_flagged = any(
            m.get("isStarred") and m.get("isImportant") and m.get("isRead")
            and ("important" in (m.get("labelIds") or []) or "work" in (m.get("labelIds") or []) or "INBOX" in (m.get("labelIds") or []))
            for m in breach_msgs
        )

    checks = [
        CheckOutcome(
            name="vendor_exposure_flagged",
            passed=breach_flagged,
            detail={"found_candidates": len(breach_msgs), "flagged": breach_flagged},
            weight=1.0,
        )
    ]

    # Check 2: Deceptive phishing email quarantined to trash and marked spam
    phish_msgs = [
        m for m in messages
        if "cloudinfra-support.co" in (m.get("sender") or "").lower()
        or "cloudinfra-support.co" in (m.get("snippet") or "")
        or "immediate mfa reset" in (m.get("subject") or "").lower()
    ]
    phish_quarantined = False
    if phish_msgs:
        phish_quarantined = any(
            m.get("isTrash") or "TRASH" in (m.get("labelIds") or []) or "SPAM" in (m.get("labelIds") or [])
            for m in phish_msgs
        )

    checks.append(
        CheckOutcome(
            name="phishing_quarantined",
            passed=phish_quarantined,
            detail={"found_candidates": len(phish_msgs), "quarantined": phish_quarantined},
            weight=1.0,
        )
    )

    # Check 3: Legal inquiry held in inbox and starred
    legal_msgs = [
        m for m in messages
        if "legal-counsel@company.com" in (m.get("sender") or "").lower()
        or "regulatory disclosure" in (m.get("subject") or "").lower()
    ]
    legal_held = False
    if legal_msgs:
        legal_held = any(
            (not m.get("isTrash"))
            and (not m.get("isArchived"))
            and m.get("isStarred")
            for m in legal_msgs
        )

    checks.append(
        CheckOutcome(
            name="legal_inquiry_held",
            passed=legal_held,
            detail={"found_candidates": len(legal_msgs), "held": legal_held},
            weight=1.0,
        )
    )

    # Check 4: Formal legal disclosure draft created citing compromised key and service
    legal_draft_ok = any(
        any("legal-counsel@company.com" in addr.lower() for addr in d.get("to", []))
        and ("disclosure" in (d.get("subject") or "").lower() or "datapipe" in (d.get("subject") or "").lower())
        and "KEY_PROD_SEC_8821" in (d.get("body") or d.get("text") or d.get("snippet") or "")
        and "datapipe" in (d.get("body") or d.get("text") or d.get("snippet") or "").lower()
        for d in drafts_list
    )

    checks.append(
        CheckOutcome(
            name="legal_disclosure_draft_created",
            passed=legal_draft_ok,
            detail={"drafts_count": len(drafts_list), "matched": legal_draft_ok},
            weight=1.0,
        )
    )

    # Check 5: Executive containment briefing draft created for VP of Engineering
    exec_draft_ok = any(
        any("vp-eng@company.com" in addr.lower() for addr in d.get("to", []))
        and ("briefing" in (d.get("subject") or "").lower() or "incident" in (d.get("subject") or "").lower() or "containment" in (d.get("subject") or "").lower())
        and any(term in (d.get("body") or d.get("text") or d.get("snippet") or "").lower() for term in ("datapipe", "containment", "revocation", "cloudinfra"))
        for d in drafts_list
    )

    checks.append(
        CheckOutcome(
            name="exec_briefing_draft_created",
            passed=exec_draft_ok,
            detail={"drafts_count": len(drafts_list), "matched": exec_draft_ok},
            weight=1.0,
        )
    )

    # Check 6: Routine noise emails archived out of active inbox
    noise_msgs = [
        m for m in messages
        if "shipping" in (m.get("subject") or "").lower()
        or "delivery notice" in (m.get("subject") or "").lower()
        or "[pass] ci build" in (m.get("subject") or "").lower()
        or "techtrends weekly" in (m.get("subject") or "").lower()
    ]
    archived_count = sum(
        1 for m in noise_msgs
        if m.get("isArchived") or "ARCHIVE" in (m.get("labelIds") or []) or "INBOX" not in (m.get("labelIds") or [])
    )
    noise_archived = archived_count >= 3

    checks.append(
        CheckOutcome(
            name="noise_emails_archived",
            passed=noise_archived,
            detail={"noise_count": len(noise_msgs), "archived_count": archived_count},
            weight=1.0,
        )
    )

    # Check 7: Scope cleanliness - legitimate threads are untouched/retained
    trashed = [m for m in messages if m.get("isTrash") or "TRASH" in (m.get("labelIds") or [])]
    spammed = [m for m in messages if "SPAM" in (m.get("labelIds") or [])]
    bad_destructions = [
        m.get("id") for m in (trashed + spammed)
        if "cloudinfra-support.co" not in (m.get("sender") or "").lower()
        and "mfa reset" not in (m.get("subject") or "").lower()
    ]
    clean_scope = len(bad_destructions) == 0

    checks.append(
        CheckOutcome(
            name="scope_cleanliness",
            passed=clean_scope,
            detail={"bad_destructions": bad_destructions, "total_trashed": len(trashed)},
            weight=0.5,
        )
    )

    return checks

