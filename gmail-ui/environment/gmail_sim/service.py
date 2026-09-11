"""Authoritative backend service for the Gmail simulation environment."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from gmail_sim.clock import now
from gmail_sim.seed import seed_database
from gmail_sim.sqlite_common import (
    NotFoundError,
    UnknownToolError,
    ValidationError,
    get_connection,
    storage_errors,
)
from gmail_sim.tracker import log_action

DEFAULT_DB_PATH = Path("/var/lib/gmail/gmail.db")
DEFAULT_SNAPSHOT_PATH = Path("/var/lib/gmail/gmail_seed_snapshot.sql")

TOOL_NAMES = (
    "list_emails",
    "get_email",
    "send_email",
    "update_email",
    "list_threads",
    "get_thread",
    "reply_thread",
    "list_drafts",
    "create_draft",
    "update_draft",
    "send_draft",
    "delete_draft",
    "list_labels",
    "create_label",
    "search_emails",
    "list_contacts",
    "get_counters",
    "submit_task",
)


def _normalize_addresses(addrs: Any) -> list[str]:
    if not addrs:
        return []
    if isinstance(addrs, str):
        return [addrs]
    return [str(a) for a in addrs]


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _row_to_email(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": r["id"],
        "threadId": r["thread_id"],
        "from": r["from_address"],
        "sender": r["from_address"],
        "to": json.loads(r["to_addresses"]),
        "cc": json.loads(r["cc_addresses"]),
        "bcc": json.loads(r["bcc_addresses"]),
        "subject": r["subject"],
        "text": r["text"],
        "body": r["text"],
        "html": r["html"],
        "date": r["date_iso"],
        "isRead": bool(r["is_read"]),
        "isStarred": bool(r["is_starred"]),
        "isImportant": bool(r["is_important"]),
        "isArchived": bool(r["is_archived"]),
        "isTrash": bool(r["is_trash"]),
        "snoozeUntil": r["snooze_until"],
        "labelIds": json.loads(r["label_ids"]),
    }


def _row_to_draft(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": r["id"],
        "to": json.loads(r["to_addresses"]),
        "cc": json.loads(r["cc_addresses"]),
        "bcc": json.loads(r["bcc_addresses"]),
        "subject": r["subject"],
        "text": r["text"],
        "body": r["text"],
        "date": r["date_iso"],
    }


def list_emails(conn: sqlite3.Connection, filters: dict[str, Any]) -> dict[str, Any]:
    query = "SELECT * FROM emails WHERE is_trash = 0"
    params: list[Any] = []

    folder = filters.get("folder")
    if folder == "inbox":
        query += " AND is_archived = 0 AND label_ids LIKE '%\"INBOX\"%'"
    elif folder == "sent":
        query += " AND label_ids LIKE '%\"SENT\"%'"
    elif folder == "archive":
        query += " AND is_archived = 1"
    elif folder == "trash":
        query = "SELECT * FROM emails WHERE is_trash = 1"
    elif folder == "starred":
        query += " AND is_starred = 1"
    elif folder == "important":
        query += " AND is_important = 1"

    if filters.get("starred"):
        query += " AND is_starred = 1"
    if filters.get("important"):
        query += " AND is_important = 1"
    if filters.get("unread") is not None:
        val = 0 if filters["unread"] else 1
        query += " AND is_read = ?"
        params.append(val)

    if filters.get("q"):
        term = f"%{filters['q']}%"
        query += " AND (subject LIKE ? OR text LIKE ? OR from_address LIKE ?)"
        params.extend([term, term, term])

    if filters.get("label"):
        query += " AND label_ids LIKE ?"
        params.append(f'%"{filters["label"]}"%')

    query += " ORDER BY date_iso DESC"
    rows = conn.execute(query, params).fetchall()
    return {"messages": [_row_to_email(r) for r in rows]}


def get_email(conn: sqlite3.Connection, email_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
    if not row:
        raise NotFoundError(f"Email with id '{email_id}' not found.")
    return {"message": _row_to_email(row)}


def send_email(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    msg_id = _generate_id("MSG")
    thread_id = args.get("parent_thread_id") or _generate_id("T")
    ts = now(conn)

    sender = "you@example.com"
    to_addrs = _normalize_addresses(args.get("to"))
    cc_addrs = _normalize_addresses(args.get("cc"))
    bcc_addrs = _normalize_addresses(args.get("bcc"))
    subject = args.get("subject") or ""
    text = args.get("body") or args.get("text") or ""
    labels = ["SENT"]

    # Thread record
    conn.execute(
        """
        INSERT OR REPLACE INTO threads (id, subject, last_activity_iso, snippet)
        VALUES (?, ?, ?, ?)
        """,
        (thread_id, subject, ts, text[:80]),
    )

    conn.execute(
        """
        INSERT INTO emails (
            id, thread_id, from_address, to_addresses, cc_addresses, bcc_addresses,
            subject, text, html, date_iso, is_read, is_starred, is_important,
            is_archived, is_trash, snooze_until, label_ids
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0, 0, 0, NULL, ?)
        """,
        (
            msg_id, thread_id, sender, json.dumps(to_addrs), json.dumps(cc_addrs),
            json.dumps(bcc_addrs), subject, text, f"<p>{text}</p>", ts, json.dumps(labels),
        ),
    )

    log_action(conn, "send_email", msg_id, {"subject": subject, "to": to_addrs})
    return {"id": msg_id, "threadId": thread_id, "status": "sent"}


def update_email(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    msg_id = args["id"]
    row = conn.execute("SELECT * FROM emails WHERE id = ?", (msg_id,)).fetchone()
    if not row:
        raise NotFoundError(f"Email with id '{msg_id}' not found.")

    labels = set(json.loads(row["label_ids"]))
    is_read = row["is_read"]
    is_starred = row["is_starred"]
    is_important = row["is_important"]
    is_archived = row["is_archived"]
    is_trash = row["is_trash"]

    if "isRead" in args:
        is_read = 1 if args["isRead"] else 0
    if "isStarred" in args:
        is_starred = 1 if args["isStarred"] else 0
        if is_starred:
            labels.add("STARRED")
        else:
            labels.discard("STARRED")
    if "isImportant" in args:
        is_important = 1 if args["isImportant"] else 0
        if is_important:
            labels.add("IMPORTANT")
        else:
            labels.discard("IMPORTANT")
    if "isArchived" in args:
        is_archived = 1 if args["isArchived"] else 0
        if is_archived:
            labels.discard("INBOX")
            labels.add("ARCHIVE")
    if "isTrash" in args:
        is_trash = 1 if args["isTrash"] else 0
        if is_trash:
            labels.discard("INBOX")
            labels.add("TRASH")

    action = args.get("action")
    if action == "archive":
        is_archived = 1
        labels.discard("INBOX")
        labels.add("ARCHIVE")
    elif action == "trash":
        is_trash = 1
        labels.discard("INBOX")
        labels.add("TRASH")
    elif action == "restore":
        is_trash = 0
        labels.discard("TRASH")
        labels.add("INBOX")

    if "addLabels" in args:
        for l in args["addLabels"]:
            labels.add(l)
    if "removeLabels" in args:
        for l in args["removeLabels"]:
            labels.discard(l)

    conn.execute(
        """
        UPDATE emails
        SET is_read = ?, is_starred = ?, is_important = ?, is_archived = ?, is_trash = ?, label_ids = ?
        WHERE id = ?
        """,
        (is_read, is_starred, is_important, is_archived, is_trash, json.dumps(sorted(labels)), msg_id),
    )

    log_action(conn, "update_email", msg_id, args)
    refreshed = conn.execute("SELECT * FROM emails WHERE id = ?", (msg_id,)).fetchone()
    return {"message": _row_to_email(refreshed)}


def list_threads(conn: sqlite3.Connection, filters: dict[str, Any]) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM threads ORDER BY last_activity_iso DESC").fetchall()
    threads_list = []
    for r in rows:
        msgs = conn.execute("SELECT * FROM emails WHERE thread_id = ? ORDER BY date_iso ASC", (r["id"],)).fetchall()
        threads_list.append({
            "id": r["id"],
            "subject": r["subject"],
            "lastActivity": r["last_activity_iso"],
            "snippet": r["snippet"],
            "messageCount": len(msgs),
            "messages": [_row_to_email(m) for m in msgs],
        })
    return {"threads": threads_list}


def get_thread(conn: sqlite3.Connection, thread_id: str) -> dict[str, Any]:
    t_row = conn.execute("SELECT * FROM threads WHERE id = ?", (thread_id,)).fetchone()
    if not t_row:
        raise NotFoundError(f"Thread with id '{thread_id}' not found.")
    msgs = conn.execute("SELECT * FROM emails WHERE thread_id = ? ORDER BY date_iso ASC", (thread_id,)).fetchall()
    return {
        "thread": {
            "id": t_row["id"],
            "subject": t_row["subject"],
            "lastActivity": t_row["last_activity_iso"],
            "snippet": t_row["snippet"],
            "messages": [_row_to_email(m) for m in msgs],
        }
    }


def reply_thread(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    t_id = args["thread_id"]
    t_row = conn.execute("SELECT * FROM threads WHERE id = ?", (t_id,)).fetchone()
    if not t_row:
        raise NotFoundError(f"Thread with id '{t_id}' not found.")

    msg_id = _generate_id("MSG")
    ts = now(conn)
    text = args.get("body") or args.get("text") or ""
    to_addrs = _normalize_addresses(args.get("to") or ["alex.smith@example.com"])

    conn.execute(
        """
        INSERT INTO emails (
            id, thread_id, from_address, to_addresses, cc_addresses, bcc_addresses,
            subject, text, html, date_iso, is_read, is_starred, is_important,
            is_archived, is_trash, snooze_until, label_ids
        )
        VALUES (?, ?, 'you@example.com', ?, '[]', '[]', ?, ?, ?, ?, 1, 0, 0, 0, 0, NULL, '["SENT"]')
        """,
        (msg_id, t_id, json.dumps(to_addrs), f"Re: {t_row['subject']}", text, f"<p>{text}</p>", ts),
    )
    conn.execute("UPDATE threads SET last_activity_iso = ?, snippet = ? WHERE id = ?", (ts, text[:80], t_id))

    log_action(conn, "reply_thread", t_id, {"message_id": msg_id, "text": text})
    return {"id": msg_id, "threadId": t_id, "status": "sent"}


def list_drafts(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM drafts ORDER BY date_iso DESC").fetchall()
    return {"drafts": [_row_to_draft(r) for r in rows]}


def create_draft(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    draft_id = _generate_id("DRAFT")
    ts = now(conn)
    to_addrs = _normalize_addresses(args.get("to"))
    cc_addrs = _normalize_addresses(args.get("cc"))
    bcc_addrs = _normalize_addresses(args.get("bcc"))
    subject = args.get("subject") or ""
    text = args.get("body") or args.get("text") or ""

    conn.execute(
        """
        INSERT INTO drafts (id, to_addresses, cc_addresses, bcc_addresses, subject, text, html, date_iso)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (draft_id, json.dumps(to_addrs), json.dumps(cc_addrs), json.dumps(bcc_addrs), subject, text, f"<p>{text}</p>", ts),
    )

    log_action(conn, "create_draft", draft_id, {"subject": subject, "to": to_addrs})
    return {
        "draft": {
            "id": draft_id,
            "to": to_addrs,
            "subject": subject,
            "text": text,
            "body": text,
            "date": ts,
        }
    }


def update_draft(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    d_id = args["id"]
    row = conn.execute("SELECT * FROM drafts WHERE id = ?", (d_id,)).fetchone()
    if not row:
        raise NotFoundError(f"Draft with id '{d_id}' not found.")

    to_addrs = args.get("to") if "to" in args else json.loads(row["to_addresses"])
    subject = args.get("subject") if "subject" in args else row["subject"]
    text = (args.get("body") or args.get("text")) if ("body" in args or "text" in args) else row["text"]

    conn.execute(
        "UPDATE drafts SET to_addresses = ?, subject = ?, text = ?, html = ? WHERE id = ?",
        (json.dumps(to_addrs), subject, text, f"<p>{text}</p>", d_id),
    )
    log_action(conn, "update_draft", d_id, args)
    return {"id": d_id, "updated": True}


def send_draft(conn: sqlite3.Connection, draft_id: str) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
    if not row:
        raise NotFoundError(f"Draft with id '{draft_id}' not found.")

    res = send_email(conn, {
        "to": json.loads(row["to_addresses"]),
        "cc": json.loads(row["cc_addresses"]),
        "bcc": json.loads(row["bcc_addresses"]),
        "subject": row["subject"],
        "text": row["text"],
    })
    conn.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    log_action(conn, "send_draft", draft_id, {"message_id": res["id"]})
    return res


def delete_draft(conn: sqlite3.Connection, draft_id: str) -> dict[str, Any]:
    conn.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    log_action(conn, "delete_draft", draft_id, {})
    return {"id": draft_id, "deleted": True}


def list_labels(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM labels").fetchall()
    return {
        "labels": [
            {"id": r["id"], "name": r["name"], "type": r["type"], "color": r["color"]}
            for r in rows
        ]
    }


def create_label(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    name = args["name"]
    lid = name.lower().replace(" ", "_")
    color = args.get("color") or "#4285F4"
    conn.execute(
        "INSERT OR REPLACE INTO labels (id, name, type, color) VALUES (?, ?, 'USER', ?)",
        (lid, name, color),
    )
    log_action(conn, "create_label", lid, {"name": name, "color": color})
    return {"label": {"id": lid, "name": name, "type": "USER", "color": color}}


def search_emails(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    query_text = args.get("query") or ""
    return list_emails(conn, {"q": query_text})


def list_contacts(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM contacts").fetchall()
    return {
        "contacts": [
            {"email": r["email"], "name": r["name"]} for r in rows
        ]
    }


def get_counters(conn: sqlite3.Connection) -> dict[str, Any]:
    unread_inbox = conn.execute(
        "SELECT COUNT(*) FROM emails WHERE is_read = 0 AND is_trash = 0 AND is_archived = 0 AND label_ids LIKE '%\"INBOX\"%'"
    ).fetchone()[0]
    total_inbox = conn.execute(
        "SELECT COUNT(*) FROM emails WHERE is_trash = 0 AND is_archived = 0 AND label_ids LIKE '%\"INBOX\"%'"
    ).fetchone()[0]
    total_starred = conn.execute("SELECT COUNT(*) FROM emails WHERE is_starred = 1 AND is_trash = 0").fetchone()[0]
    total_drafts = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]

    return {
        "unread": unread_inbox,
        "totalInbox": total_inbox,
        "starred": total_starred,
        "drafts": total_drafts,
    }


def submit_task(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    log_action(conn, "submit_task", None, args)
    return {
        "submitted": True,
        "summary": args.get("summary", ""),
        "affected_message_ids": args.get("affected_message_ids", []),
    }


def export_state(conn: sqlite3.Connection) -> dict[str, Any]:
    emails_res = conn.execute("SELECT * FROM emails ORDER BY date_iso ASC").fetchall()
    threads_res = conn.execute("SELECT * FROM threads ORDER BY last_activity_iso ASC").fetchall()
    labels_res = conn.execute("SELECT * FROM labels").fetchall()
    settings_res = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    contacts_res = conn.execute("SELECT * FROM contacts").fetchall()
    drafts_res = conn.execute("SELECT * FROM drafts ORDER BY date_iso ASC").fetchall()

    contacts_map = {r["email"]: {"email": r["email"], "name": r["name"]} for r in contacts_res}

    actions_res = conn.execute("SELECT * FROM action_log ORDER BY id ASC").fetchall()

    return {
        "messages": [_row_to_email(r) for r in emails_res],
        "threads": [
            {
                "id": r["id"],
                "subject": r["subject"],
                "lastActivity": r["last_activity_iso"],
                "snippet": r["snippet"],
            }
            for r in threads_res
        ],
        "labels": [
            {"id": r["id"], "name": r["name"], "type": r["type"], "color": r["color"]}
            for r in labels_res
        ],
        "drafts": [_row_to_draft(r) for r in drafts_res],
        "settings": {
            "displayName": settings_res["display_name"] if settings_res else "You",
            "email": settings_res["email"] if settings_res else "you@example.com",
            "signature": settings_res["signature"] if settings_res else "",
        },
        "contacts": contacts_map,
        "action_log": [
            {
                "id": r["id"],
                "action": r["action"],
                "tool_name": r["action"],
                "target_id": r["target_id"],
                "payload": json.loads(r["payload"]),
                "timestamp": r["ts_iso"],
            }
            for r in actions_res
        ],
    }


def execute_tool(db_path: Path | str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    with storage_errors():
        with get_connection(db_path) as conn:
            if tool_name == "list_emails":
                return list_emails(conn, arguments)
            elif tool_name == "get_email":
                return get_email(conn, arguments["id"])
            elif tool_name == "send_email":
                return send_email(conn, arguments)
            elif tool_name == "update_email":
                return update_email(conn, arguments)
            elif tool_name == "list_threads":
                return list_threads(conn, arguments)
            elif tool_name == "get_thread":
                return get_thread(conn, arguments["id"])
            elif tool_name == "reply_thread":
                return reply_thread(conn, arguments)
            elif tool_name == "list_drafts":
                return list_drafts(conn)
            elif tool_name == "create_draft":
                return create_draft(conn, arguments)
            elif tool_name == "update_draft":
                return update_draft(conn, arguments)
            elif tool_name == "send_draft":
                return send_draft(conn, arguments["id"])
            elif tool_name == "delete_draft":
                return delete_draft(conn, arguments["id"])
            elif tool_name == "list_labels":
                return list_labels(conn)
            elif tool_name == "create_label":
                return create_label(conn, arguments)
            elif tool_name == "search_emails":
                return search_emails(conn, arguments)
            elif tool_name == "list_contacts":
                return list_contacts(conn)
            elif tool_name == "get_counters":
                return get_counters(conn)
            elif tool_name == "submit_task":
                return submit_task(conn, arguments)
            else:
                raise UnknownToolError(f"Unknown tool: '{tool_name}'")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Gmail service CLI")
    subparsers = parser.add_subparsers(dest="command")
    seed_parser = subparsers.add_parser("seed", help="Seed the Gmail database")
    seed_parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to sqlite db")
    seed_parser.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT_PATH), help="Path to snapshot sql")
    seed_parser.add_argument("--seed", default="gmail", help="Random seed")

    args = parser.parse_args()
    if args.command == "seed":
        seed_database(args.db, snapshot_path=args.snapshot, seed=args.seed)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
