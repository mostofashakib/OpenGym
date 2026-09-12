"""Authoritative backend service for the Gmail simulation environment."""

from __future__ import annotations

import json
import shlex
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
        if "," in addrs:
            return [a.strip() for a in addrs.split(",") if a.strip()]
        return [addrs.strip()]
    if isinstance(addrs, (list, tuple, set)):
        res: list[str] = []
        for a in addrs:
            if isinstance(a, str) and "," in a:
                res.extend(p.strip() for p in a.split(",") if p.strip())
            else:
                res.append(str(a).strip())
        return res
    return [str(addrs).strip()]


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _row_to_email(r: sqlite3.Row) -> dict[str, Any]:
    to_list = json.loads(r["to_addresses"])
    cc_list = json.loads(r["cc_addresses"])
    bcc_list = json.loads(r["bcc_addresses"])
    label_list = json.loads(r["label_ids"])
    return {
        "id": r["id"],
        "email_id": r["id"],
        "threadId": r["thread_id"],
        "thread_id": r["thread_id"],
        "from": r["from_address"],
        "sender": r["from_address"],
        "from_address": r["from_address"],
        "to": to_list,
        "to_addresses": to_list,
        "cc": cc_list,
        "cc_addresses": cc_list,
        "bcc": bcc_list,
        "bcc_addresses": bcc_list,
        "subject": r["subject"],
        "text": r["text"],
        "body": r["text"],
        "html": r["html"],
        "date": r["date_iso"],
        "date_iso": r["date_iso"],
        "isRead": bool(r["is_read"]),
        "is_read": bool(r["is_read"]),
        "isStarred": bool(r["is_starred"]),
        "is_starred": bool(r["is_starred"]),
        "isImportant": bool(r["is_important"]),
        "is_important": bool(r["is_important"]),
        "isArchived": bool(r["is_archived"]),
        "is_archived": bool(r["is_archived"]),
        "isTrash": bool(r["is_trash"]),
        "is_trash": bool(r["is_trash"]),
        "snoozeUntil": r["snooze_until"],
        "snooze_until": r["snooze_until"],
        "labelIds": label_list,
        "label_ids": label_list,
        "labels": label_list,
    }


def _row_to_draft(r: sqlite3.Row) -> dict[str, Any]:
    to_list = json.loads(r["to_addresses"])
    cc_list = json.loads(r["cc_addresses"])
    bcc_list = json.loads(r["bcc_addresses"])
    return {
        "id": r["id"],
        "draft_id": r["id"],
        "to": to_list,
        "to_addresses": to_list,
        "cc": cc_list,
        "cc_addresses": cc_list,
        "bcc": bcc_list,
        "bcc_addresses": bcc_list,
        "subject": r["subject"],
        "text": r["text"],
        "body": r["text"],
        "date": r["date_iso"],
        "date_iso": r["date_iso"],
    }


def _parse_single_token(raw_token: str) -> tuple[str, list[Any], bool]:
    """Parse a single search token into a SQL WHERE clause and parameter list."""
    negated = False
    token = raw_token.strip()
    if not token:
        return "", [], False
    if token.startswith("-") and len(token) > 1:
        negated = True
        token = token[1:].strip()

    token_lower = token.lower()
    includes_trash = False

    if token_lower.startswith("from:"):
        val = token[5:].strip("'\"")
        clause = "from_address NOT LIKE ?" if negated else "from_address LIKE ?"
        return clause, [f"%{val}%"], False

    elif token_lower.startswith("to:"):
        val = token[3:].strip("'\"")
        clause = "to_addresses NOT LIKE ?" if negated else "to_addresses LIKE ?"
        return clause, [f"%{val}%"], False

    elif token_lower.startswith("cc:"):
        val = token[3:].strip("'\"")
        clause = "cc_addresses NOT LIKE ?" if negated else "cc_addresses LIKE ?"
        return clause, [f"%{val}%"], False

    elif token_lower.startswith("bcc:"):
        val = token[4:].strip("'\"")
        clause = "bcc_addresses NOT LIKE ?" if negated else "bcc_addresses LIKE ?"
        return clause, [f"%{val}%"], False

    elif token_lower.startswith("subject:"):
        val = token[8:].strip("'\"")
        clause = "subject NOT LIKE ?" if negated else "subject LIKE ?"
        return clause, [f"%{val}%"], False

    elif token_lower.startswith("label:"):
        val = token[6:].strip("'\"")
        clause = "label_ids NOT LIKE ?" if negated else "label_ids LIKE ?"
        return clause, [f'%"{val}"%'], False

    elif token_lower.startswith("in:"):
        val = token[3:].strip("'\"").lower()
        if val == "inbox":
            clause = "(is_archived = 1 OR label_ids NOT LIKE '%\"INBOX\"%')" if negated else "is_archived = 0 AND label_ids LIKE '%\"INBOX\"%'"
            return clause, [], False
        elif val == "sent":
            clause = "label_ids NOT LIKE '%\"SENT\"%'" if negated else "label_ids LIKE '%\"SENT\"%'"
            return clause, [], False
        elif val in ("archive", "archived"):
            clause = "is_archived = 0" if negated else "is_archived = 1"
            return clause, [], False
        elif val in ("trash", "bin"):
            includes_trash = True
            clause = "is_trash = 0" if negated else "is_trash = 1"
            return clause, [], includes_trash
        elif val == "starred":
            clause = "is_starred = 0" if negated else "is_starred = 1"
            return clause, [], False
        elif val == "important":
            clause = "is_important = 0" if negated else "is_important = 1"
            return clause, [], False
        elif val in ("draft", "drafts"):
            clause = "label_ids NOT LIKE '%\"DRAFTS\"%'" if negated else "label_ids LIKE '%\"DRAFTS\"%'"
            return clause, [], False
        elif val in ("all", "anywhere"):
            return "1=1", [], True
        else:
            clause = "label_ids NOT LIKE ?" if negated else "label_ids LIKE ?"
            return clause, [f'%"{val}"%'], False

    elif token_lower.startswith("is:"):
        val = token[3:].strip("'\"").lower()
        if val == "unread":
            clause = "is_read = 1" if negated else "is_read = 0"
            return clause, [], False
        elif val == "read":
            clause = "is_read = 0" if negated else "is_read = 1"
            return clause, [], False
        elif val == "starred":
            clause = "is_starred = 0" if negated else "is_starred = 1"
            return clause, [], False
        elif val == "unstarred":
            clause = "is_starred = 1" if negated else "is_starred = 0"
            return clause, [], False
        elif val == "important":
            clause = "is_important = 0" if negated else "is_important = 1"
            return clause, [], False
        elif val in ("archive", "archived"):
            clause = "is_archived = 0" if negated else "is_archived = 1"
            return clause, [], False
        elif val == "trash":
            includes_trash = True
            clause = "is_trash = 0" if negated else "is_trash = 1"
            return clause, [], includes_trash
        elif val == "sent":
            clause = "label_ids NOT LIKE '%\"SENT\"%'" if negated else "label_ids LIKE '%\"SENT\"%'"
            return clause, [], False
        elif val in ("draft", "drafts"):
            clause = "label_ids NOT LIKE '%\"DRAFTS\"%'" if negated else "label_ids LIKE '%\"DRAFTS\"%'"
            return clause, [], False

    elif token_lower.startswith("has:"):
        val = token[4:].strip("'\"").lower()
        if val in ("attachment", "drive", "document", "file"):
            clause = "(text NOT LIKE '%attach%' AND html NOT LIKE '%attach%')" if negated else "(text LIKE '%attach%' OR html LIKE '%attach%')"
            return clause, [], False

    elif token_lower.startswith("after:") or token_lower.startswith("newer:"):
        val = token.split(":", 1)[1].strip("'\"").replace("/", "-")
        clause = "date_iso < ?" if negated else "date_iso >= ?"
        return clause, [val], False

    elif token_lower.startswith("before:") or token_lower.startswith("older:"):
        val = token.split(":", 1)[1].strip("'\"").replace("/", "-")
        clause = "date_iso > ?" if negated else "date_iso <= ?"
        return clause, [val], False

    # Free-text search term
    term = f"%{token.strip('\"\'')}%"
    if negated:
        clause = "(subject NOT LIKE ? AND text NOT LIKE ? AND from_address NOT LIKE ? AND to_addresses NOT LIKE ?)"
    else:
        clause = "(subject LIKE ? OR text LIKE ? OR from_address LIKE ? OR to_addresses LIKE ?)"
    return clause, [term, term, term, term], False


def _parse_search_query(q_str: str) -> tuple[list[str], list[Any], bool]:
    """Parse Gmail-style search query into SQL WHERE clauses and parameters.

    Supports:
    - from:<addr>
    - to:<addr>, cc:<addr>, bcc:<addr>
    - subject:<text>
    - label:<name>
    - in:<folder> (inbox, sent, archive, trash, starred, important, all)
    - is:<status> (unread, read, starred, unstarred, important, archived, trash)
    - has:attachment
    - after:<date>, before:<date>, newer:<date>, older:<date>
    - OR expressions (e.g. 'term1 OR term2')
    - Negations with leading '-' (e.g. -is:read, -from:spam.com)
    - Free-text terms (with or without quotes) matching subject, body, from, or to.
    """
    if not q_str:
        return [], [], False

    try:
        tokens = shlex.split(q_str)
    except Exception:
        tokens = q_str.split()

    clauses: list[str] = []
    params: list[Any] = []
    includes_trash = False

    i = 0
    while i < len(tokens):
        raw_token = tokens[i].strip()
        if not raw_token:
            i += 1
            continue

        # Check if next token is OR
        if i + 2 < len(tokens) and tokens[i + 1].upper() == "OR":
            c1, p1, tr1 = _parse_single_token(raw_token)
            c2, p2, tr2 = _parse_single_token(tokens[i + 2].strip())
            if c1 and c2:
                clauses.append(f"({c1} OR {c2})")
                params.extend(p1)
                params.extend(p2)
                if tr1 or tr2:
                    includes_trash = True
                i += 3
                continue

        c, p, tr = _parse_single_token(raw_token)
        if c:
            clauses.append(c)
            params.extend(p)
            if tr:
                includes_trash = True
        i += 1

    return clauses, params, includes_trash


def list_emails(conn: sqlite3.Connection, filters: dict[str, Any]) -> dict[str, Any]:
    q_str = str(filters.get("q") or filters.get("query") or filters.get("search") or "").strip()
    q_clauses, q_params, includes_trash = _parse_search_query(q_str)

    folder = str(filters.get("folder") or "").lower()
    if folder in ("trash", "bin") or includes_trash:
        base_query = "SELECT * FROM emails WHERE 1=1"
        if not includes_trash and folder in ("trash", "bin"):
            q_clauses.append("is_trash = 1")
    else:
        base_query = "SELECT * FROM emails WHERE is_trash = 0"

    if folder == "inbox":
        q_clauses.append("is_archived = 0 AND label_ids LIKE '%\"INBOX\"%'")
    elif folder == "sent":
        q_clauses.append("label_ids LIKE '%\"SENT\"%'")
    elif folder in ("archive", "archived"):
        q_clauses.append("is_archived = 1")
    elif folder == "starred":
        q_clauses.append("is_starred = 1")
    elif folder == "important":
        q_clauses.append("is_important = 1")

    # Flag filters (camelCase and snake_case)
    starred = filters.get("starred") if "starred" in filters else filters.get("isStarred") if "isStarred" in filters else filters.get("is_starred")
    if starred is not None:
        q_clauses.append("is_starred = 1" if starred else "is_starred = 0")

    important = filters.get("important") if "important" in filters else filters.get("isImportant") if "isImportant" in filters else filters.get("is_important")
    if important is not None:
        q_clauses.append("is_important = 1" if important else "is_important = 0")

    unread = filters.get("unread") if "unread" in filters else filters.get("isUnread") if "isUnread" in filters else filters.get("is_unread")
    read = filters.get("read") if "read" in filters else filters.get("isRead") if "isRead" in filters else filters.get("is_read")
    if unread is not None:
        q_clauses.append("is_read = 0" if unread else "is_read = 1")
    elif read is not None:
        q_clauses.append("is_read = 1" if read else "is_read = 0")

    label = filters.get("label") or filters.get("label_id") or filters.get("labelId")
    if label:
        q_clauses.append("label_ids LIKE ?")
        q_params.append(f'%"{label}"%')

    sender = filters.get("from") or filters.get("from_address") or filters.get("sender")
    if sender:
        q_clauses.append("from_address LIKE ?")
        q_params.append(f"%{sender}%")

    to_addr = filters.get("to") or filters.get("to_address") or filters.get("recipient")
    if to_addr:
        q_clauses.append("to_addresses LIKE ?")
        q_params.append(f"%{to_addr}%")

    subject = filters.get("subject")
    if subject:
        q_clauses.append("subject LIKE ?")
        q_params.append(f"%{subject}%")

    if q_clauses:
        base_query += " AND " + " AND ".join(q_clauses)

    base_query += " ORDER BY date_iso DESC"
    rows = conn.execute(base_query, q_params).fetchall()
    return {"messages": [_row_to_email(r) for r in rows]}


def get_email(conn: sqlite3.Connection, email_id: str | dict[str, Any]) -> dict[str, Any]:
    eid = email_id if isinstance(email_id, str) else str(
        email_id.get("id") or email_id.get("email_id") or email_id.get("message_id") or email_id.get("messageId") or ""
    )
    if not eid:
        raise ValidationError("Missing required email ID.")
    row = conn.execute("SELECT * FROM emails WHERE id = ?", (eid,)).fetchone()
    if not row:
        raise NotFoundError(f"Email with id '{eid}' not found.")
    email_data = _row_to_email(row)
    return {"message": email_data, "id": email_data["id"]}


def send_email(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    msg_id = _generate_id("MSG")
    thread_id = (
        args.get("parent_thread_id")
        or args.get("thread_id")
        or args.get("threadId")
        or _generate_id("T")
    )
    ts = now(conn)

    sender = "you@example.com"
    to_addrs = _normalize_addresses(args.get("to") or args.get("to_addresses") or args.get("recipient"))
    cc_addrs = _normalize_addresses(args.get("cc") or args.get("cc_addresses"))
    bcc_addrs = _normalize_addresses(args.get("bcc") or args.get("bcc_addresses"))
    subject = args.get("subject") or ""
    text = args.get("body") or args.get("text") or args.get("content") or args.get("message") or ""
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
    return {"id": msg_id, "threadId": thread_id, "thread_id": thread_id, "status": "sent"}


def update_email(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    msg_id = args.get("id") or args.get("email_id") or args.get("message_id") or args.get("messageId")
    if not msg_id:
        raise ValidationError("Missing required email ID.")
    row = conn.execute("SELECT * FROM emails WHERE id = ?", (msg_id,)).fetchone()
    if not row:
        raise NotFoundError(f"Email with id '{msg_id}' not found.")

    labels = set(json.loads(row["label_ids"]))
    is_read = row["is_read"]
    is_starred = row["is_starred"]
    is_important = row["is_important"]
    is_archived = row["is_archived"]
    is_trash = row["is_trash"]

    # Read state
    read_val = None
    if "isRead" in args:
        read_val = args["isRead"]
    elif "is_read" in args:
        read_val = args["is_read"]
    elif "read" in args:
        read_val = args["read"]
    elif "unread" in args:
        read_val = not args["unread"]
    elif "is_unread" in args:
        read_val = not args["is_unread"]
    elif "isUnread" in args:
        read_val = not args["isUnread"]

    if read_val is not None:
        is_read = 1 if read_val else 0

    # Starred state
    star_val = None
    if "isStarred" in args:
        star_val = args["isStarred"]
    elif "is_starred" in args:
        star_val = args["is_starred"]
    elif "starred" in args:
        star_val = args["starred"]

    if star_val is not None:
        is_starred = 1 if star_val else 0
        if is_starred:
            labels.add("STARRED")
        else:
            labels.discard("STARRED")

    # Important state
    imp_val = None
    if "isImportant" in args:
        imp_val = args["isImportant"]
    elif "is_important" in args:
        imp_val = args["is_important"]
    elif "important" in args:
        imp_val = args["important"]

    if imp_val is not None:
        is_important = 1 if imp_val else 0
        if is_important:
            labels.add("IMPORTANT")
        else:
            labels.discard("IMPORTANT")

    # Archived state
    arch_val = None
    if "isArchived" in args:
        arch_val = args["isArchived"]
    elif "is_archived" in args:
        arch_val = args["is_archived"]
    elif "archived" in args:
        arch_val = args["archived"]

    if arch_val is not None:
        is_archived = 1 if arch_val else 0
        if is_archived:
            labels.discard("INBOX")
            labels.add("ARCHIVE")
        else:
            labels.discard("ARCHIVE")
            labels.add("INBOX")

    # Trash state
    trash_val = None
    if "isTrash" in args:
        trash_val = args["isTrash"]
    elif "is_trash" in args:
        trash_val = args["is_trash"]
    elif "trash" in args:
        trash_val = args["trash"]

    if trash_val is not None:
        is_trash = 1 if trash_val else 0
        if is_trash:
            labels.discard("INBOX")
            labels.add("TRASH")
        else:
            labels.discard("TRASH")
            labels.add("INBOX")

    action = (args.get("action") or "").lower()
    if action == "archive":
        is_archived = 1
        labels.discard("INBOX")
        labels.add("ARCHIVE")
    elif action in ("unarchive", "restore_inbox"):
        is_archived = 0
        labels.discard("ARCHIVE")
        labels.add("INBOX")
    elif action in ("trash", "delete"):
        is_trash = 1
        labels.discard("INBOX")
        labels.add("TRASH")
    elif action == "restore":
        is_trash = 0
        labels.discard("TRASH")
        labels.add("INBOX")
    elif action in ("mark_read", "read"):
        is_read = 1
    elif action in ("mark_unread", "unread"):
        is_read = 0
    elif action in ("star", "add_star"):
        is_starred = 1
        labels.add("STARRED")
    elif action in ("unstar", "remove_star"):
        is_starred = 0
        labels.discard("STARRED")
    elif action in ("mark_important", "important"):
        is_important = 1
        labels.add("IMPORTANT")
    elif action in ("unmark_important", "not_important"):
        is_important = 0
        labels.discard("IMPORTANT")

    add_labels = args.get("addLabels") or args.get("add_labels") or args.get("labels_to_add") or []
    if isinstance(add_labels, str):
        add_labels = [l.strip() for l in add_labels.split(",") if l.strip()]
    for l in add_labels:
        labels.add(l)

    remove_labels = args.get("removeLabels") or args.get("remove_labels") or args.get("labels_to_remove") or []
    if isinstance(remove_labels, str):
        remove_labels = [l.strip() for l in remove_labels.split(",") if l.strip()]
    for l in remove_labels:
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
    email_data = _row_to_email(refreshed)
    return {"message": email_data, "id": msg_id, "updated": True}


def list_threads(conn: sqlite3.Connection, filters: dict[str, Any]) -> dict[str, Any]:
    folder = str(filters.get("folder") or "").lower()
    q_str = str(filters.get("q") or filters.get("query") or "").strip()

    filter_clauses: list[str] = []
    filter_params: list[Any] = []
    includes_trash = False

    if q_str:
        q_clauses, q_params, inc_trash = _parse_search_query(q_str)
        filter_clauses.extend(q_clauses)
        filter_params.extend(q_params)
        if inc_trash:
            includes_trash = True

    if folder in ("trash", "bin") or includes_trash:
        if not includes_trash and folder in ("trash", "bin"):
            filter_clauses.append("is_trash = 1")
    else:
        filter_clauses.append("is_trash = 0")

    if folder == "inbox":
        filter_clauses.append("is_archived = 0 AND label_ids LIKE '%\"INBOX\"%'")
    elif folder == "sent":
        filter_clauses.append("label_ids LIKE '%\"SENT\"%'")
    elif folder in ("archive", "archived"):
        filter_clauses.append("is_archived = 1")
    elif folder == "starred":
        filter_clauses.append("is_starred = 1")
    elif folder == "important":
        filter_clauses.append("is_important = 1")

    if filter_clauses:
        sql = f"SELECT DISTINCT thread_id FROM emails WHERE {' AND '.join(filter_clauses)}"
        matching_tids = {r["thread_id"] for r in conn.execute(sql, filter_params).fetchall()}
        rows = conn.execute("SELECT * FROM threads ORDER BY last_activity_iso DESC").fetchall()
        rows = [r for r in rows if r["id"] in matching_tids]
    else:
        rows = conn.execute("SELECT * FROM threads ORDER BY last_activity_iso DESC").fetchall()

    threads_list = []
    for r in rows:
        msgs = conn.execute("SELECT * FROM emails WHERE thread_id = ? ORDER BY date_iso ASC", (r["id"],)).fetchall()
        threads_list.append({
            "id": r["id"],
            "thread_id": r["id"],
            "subject": r["subject"],
            "lastActivity": r["last_activity_iso"],
            "last_activity_iso": r["last_activity_iso"],
            "snippet": r["snippet"],
            "messageCount": len(msgs),
            "messages": [_row_to_email(m) for m in msgs],
        })
    return {"threads": threads_list}


def get_thread(conn: sqlite3.Connection, thread_id: str | dict[str, Any]) -> dict[str, Any]:
    tid = thread_id if isinstance(thread_id, str) else str(
        thread_id.get("id") or thread_id.get("thread_id") or thread_id.get("threadId") or ""
    )
    if not tid:
        raise ValidationError("Missing required thread ID.")
    t_row = conn.execute("SELECT * FROM threads WHERE id = ?", (tid,)).fetchone()
    if not t_row:
        raise NotFoundError(f"Thread with id '{tid}' not found.")
    msgs = conn.execute("SELECT * FROM emails WHERE thread_id = ? ORDER BY date_iso ASC", (tid,)).fetchall()
    thread_data = {
        "id": t_row["id"],
        "thread_id": t_row["id"],
        "subject": t_row["subject"],
        "lastActivity": t_row["last_activity_iso"],
        "last_activity_iso": t_row["last_activity_iso"],
        "snippet": t_row["snippet"],
        "messages": [_row_to_email(m) for m in msgs],
    }
    return {"thread": thread_data, "id": t_row["id"]}


def reply_thread(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    t_id = args.get("thread_id") or args.get("id") or args.get("threadId")
    if not t_id:
        raise ValidationError("Missing required thread_id.")
    t_row = conn.execute("SELECT * FROM threads WHERE id = ?", (t_id,)).fetchone()
    if not t_row:
        raise NotFoundError(f"Thread with id '{t_id}' not found.")

    msg_id = _generate_id("MSG")
    ts = now(conn)
    text = args.get("body") or args.get("text") or args.get("content") or ""

    if args.get("to"):
        to_addrs = _normalize_addresses(args.get("to"))
    else:
        last_msg = conn.execute(
            "SELECT from_address FROM emails WHERE thread_id = ? ORDER BY date_iso DESC LIMIT 1",
            (t_id,),
        ).fetchone()
        if last_msg and last_msg["from_address"] and last_msg["from_address"] != "you@example.com":
            to_addrs = [last_msg["from_address"]]
        else:
            to_addrs = ["alex.smith@example.com"]

    subject = t_row["subject"]
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    conn.execute(
        """
        INSERT INTO emails (
            id, thread_id, from_address, to_addresses, cc_addresses, bcc_addresses,
            subject, text, html, date_iso, is_read, is_starred, is_important,
            is_archived, is_trash, snooze_until, label_ids
        )
        VALUES (?, ?, 'you@example.com', ?, '[]', '[]', ?, ?, ?, ?, 1, 0, 0, 0, 0, NULL, '["SENT"]')
        """,
        (msg_id, t_id, json.dumps(to_addrs), subject, text, f"<p>{text}</p>", ts),
    )
    conn.execute("UPDATE threads SET last_activity_iso = ?, snippet = ? WHERE id = ?", (ts, text[:80], t_id))

    log_action(conn, "reply_thread", t_id, {"message_id": msg_id, "text": text})
    return {"id": msg_id, "threadId": t_id, "thread_id": t_id, "status": "sent"}


def list_drafts(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM drafts ORDER BY date_iso DESC").fetchall()
    return {"drafts": [_row_to_draft(r) for r in rows]}


def create_draft(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    draft_id = _generate_id("DRAFT")
    ts = now(conn)
    to_addrs = _normalize_addresses(args.get("to") or args.get("to_addresses") or args.get("recipient"))
    cc_addrs = _normalize_addresses(args.get("cc") or args.get("cc_addresses"))
    bcc_addrs = _normalize_addresses(args.get("bcc") or args.get("bcc_addresses"))
    subject = args.get("subject") or ""
    text = args.get("body") or args.get("text") or args.get("content") or args.get("message") or ""

    conn.execute(
        """
        INSERT INTO drafts (id, to_addresses, cc_addresses, bcc_addresses, subject, text, html, date_iso)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (draft_id, json.dumps(to_addrs), json.dumps(cc_addrs), json.dumps(bcc_addrs), subject, text, f"<p>{text}</p>", ts),
    )

    log_action(conn, "create_draft", draft_id, {"subject": subject, "to": to_addrs})
    draft_dict = {
        "id": draft_id,
        "draft_id": draft_id,
        "to": to_addrs,
        "cc": cc_addrs,
        "bcc": bcc_addrs,
        "subject": subject,
        "text": text,
        "body": text,
        "date": ts,
    }
    return {
        "draft": draft_dict,
        "id": draft_id,
        "draft_id": draft_id,
    }


def update_draft(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    d_id = args.get("id") or args.get("draft_id") or args.get("draftId")
    if not d_id:
        raise ValidationError("Missing required draft ID.")
    row = conn.execute("SELECT * FROM drafts WHERE id = ?", (d_id,)).fetchone()
    if not row:
        raise NotFoundError(f"Draft with id '{d_id}' not found.")

    to_addrs = _normalize_addresses(args["to"]) if "to" in args else json.loads(row["to_addresses"])
    subject = args.get("subject") if "subject" in args else row["subject"]
    text = (args.get("body") or args.get("text") or args.get("content")) if ("body" in args or "text" in args or "content" in args) else row["text"]

    conn.execute(
        "UPDATE drafts SET to_addresses = ?, subject = ?, text = ?, html = ? WHERE id = ?",
        (json.dumps(to_addrs), subject, text, f"<p>{text}</p>", d_id),
    )
    log_action(conn, "update_draft", d_id, args)
    return {"id": d_id, "draft_id": d_id, "updated": True}


def send_draft(conn: sqlite3.Connection, draft_id: str | dict[str, Any]) -> dict[str, Any]:
    did = draft_id if isinstance(draft_id, str) else str(
        draft_id.get("id") or draft_id.get("draft_id") or draft_id.get("draftId") or ""
    )
    if not did:
        raise ValidationError("Missing required draft ID.")
    row = conn.execute("SELECT * FROM drafts WHERE id = ?", (did,)).fetchone()
    if not row:
        raise NotFoundError(f"Draft with id '{did}' not found.")

    res = send_email(conn, {
        "to": json.loads(row["to_addresses"]),
        "cc": json.loads(row["cc_addresses"]),
        "bcc": json.loads(row["bcc_addresses"]),
        "subject": row["subject"],
        "text": row["text"],
    })
    conn.execute("DELETE FROM drafts WHERE id = ?", (did,))
    log_action(conn, "send_draft", did, {"message_id": res["id"]})
    return res


def delete_draft(conn: sqlite3.Connection, draft_id: str | dict[str, Any]) -> dict[str, Any]:
    did = draft_id if isinstance(draft_id, str) else str(
        draft_id.get("id") or draft_id.get("draft_id") or draft_id.get("draftId") or ""
    )
    if not did:
        raise ValidationError("Missing required draft ID.")
    conn.execute("DELETE FROM drafts WHERE id = ?", (did,))
    log_action(conn, "delete_draft", did, {})
    return {"id": did, "draft_id": did, "deleted": True}


def list_labels(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM labels").fetchall()
    return {
        "labels": [
            {"id": r["id"], "name": r["name"], "type": r["type"], "color": r["color"]}
            for r in rows
        ]
    }


def create_label(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    name = args.get("name") or ""
    lid = name.lower().replace(" ", "_")
    color = args.get("color") or "#4285F4"
    conn.execute(
        "INSERT OR REPLACE INTO labels (id, name, type, color) VALUES (?, ?, 'USER', ?)",
        (lid, name, color),
    )
    log_action(conn, "create_label", lid, {"name": name, "color": color})
    label_dict = {"id": lid, "name": name, "type": "USER", "color": color}
    return {"label": label_dict, "id": lid}


def search_emails(conn: sqlite3.Connection, args: dict[str, Any]) -> dict[str, Any]:
    query_text = args.get("query") or args.get("q") or args.get("search") or ""
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
    summary = args.get("summary") or args.get("report") or args.get("notes") or ""
    affected = (
        args.get("affected_message_ids")
        or args.get("affectedMessageIds")
        or args.get("message_ids")
        or args.get("messages")
        or []
    )
    if isinstance(affected, str):
        affected = [a.strip() for a in affected.split(",") if a.strip()]
    log_action(conn, "submit_task", None, args)
    return {
        "submitted": True,
        "summary": summary,
        "affected_message_ids": affected,
        "affectedMessageIds": affected,
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
                return get_email(conn, arguments)
            elif tool_name == "send_email":
                return send_email(conn, arguments)
            elif tool_name == "update_email":
                return update_email(conn, arguments)
            elif tool_name == "list_threads":
                return list_threads(conn, arguments)
            elif tool_name == "get_thread":
                return get_thread(conn, arguments)
            elif tool_name == "reply_thread":
                return reply_thread(conn, arguments)
            elif tool_name == "list_drafts":
                return list_drafts(conn)
            elif tool_name == "create_draft":
                return create_draft(conn, arguments)
            elif tool_name == "update_draft":
                return update_draft(conn, arguments)
            elif tool_name == "send_draft":
                return send_draft(conn, arguments)
            elif tool_name == "delete_draft":
                return delete_draft(conn, arguments)
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
