"""Core simulated enterprise workstation service layer."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from workstation_sim.clock import VirtualClock
from workstation_sim.disturbances import DisturbanceManager
from workstation_sim.sqlite_common import connect, query_rows
from workstation_sim.tracker import log_action

DEFAULT_ACTOR = "alex.mercer@apexglobal.io"


class ServiceError(Exception):
    """Business logic or validation error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _get_clock_and_disturbances(db_path: Path) -> tuple[VirtualClock, DisturbanceManager]:
    clock = VirtualClock(db_path)
    with connect(db_path) as conn:
        seed_val = int(conn.execute("SELECT value FROM system_state WHERE key = 'seed'").fetchone()[0])
    return clock, DisturbanceManager(seed=seed_val)


# ===========================================================================
# 1. Email Client
# ===========================================================================

def mail_list_threads(
    db_path: Path,
    folder: str = "inbox",
    query: str = "",
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("mail", "list_threads")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        sql = """
            SELECT t.id, t.subject, t.customer_id, t.last_activity_iso, t.snippet,
                   COUNT(e.id) as message_count,
                   MAX(e.is_read) as has_read,
                   MIN(e.is_read) as all_read
            FROM email_threads t
            JOIN emails e ON t.id = e.thread_id
            WHERE e.folder = ?
        """
        params: list[Any] = [folder]
        if query:
            sql += " AND (t.subject LIKE ? OR t.snippet LIKE ? OR e.body LIKE ?)"
            q_like = f"%{query}%"
            params.extend([q_like, q_like, q_like])
        sql += " GROUP BY t.id ORDER BY t.last_activity_iso DESC LIMIT 50"
        threads = query_rows(conn, sql, tuple(params))
        log_action(conn, clock, actor, "mail", "list_threads", "folder", folder, {"query": query})
        return {"threads": threads, "count": len(threads)}


def mail_get_thread(
    db_path: Path,
    thread_id: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("mail", "get_thread")
    with connect(db_path) as conn:
        clock.advance(15, conn)
        thread = conn.execute("SELECT * FROM email_threads WHERE id = ?", (thread_id,)).fetchone()
        if not thread:
            raise ServiceError("not_found", f"Email thread '{thread_id}' not found.")

        # Mark messages read
        conn.execute("UPDATE emails SET is_read = 1 WHERE thread_id = ?", (thread_id,))
        emails = query_rows(conn, "SELECT * FROM emails WHERE thread_id = ? ORDER BY date_iso ASC", (thread_id,))
        for e in emails:
            e["to_addrs"] = json.loads(e["to_addrs"]) if e.get("to_addrs") else []
            e["cc_addrs"] = json.loads(e["cc_addrs"]) if e.get("cc_addrs") else []
            e["attachments"] = json.loads(e["attachments"]) if e.get("attachments") else []

        log_action(conn, clock, actor, "mail", "get_thread", "thread", thread_id)
        return {
            "thread": dict(thread),
            "messages": emails,
        }


def mail_send_message(
    db_path: Path,
    to: list[str] | str,
    subject: str,
    body: str,
    cc: list[str] | str | None = None,
    thread_id: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("mail", "send_message")
    to_list = [to] if isinstance(to, str) else list(to)
    cc_list = ([cc] if isinstance(cc, str) else list(cc)) if cc else []

    with connect(db_path) as conn:
        now_iso = clock.advance(30, conn)
        tid = thread_id
        if not tid:
            tid = f"THREAD-{hashlib.md5(now_iso.encode()).hexdigest()[:8]}"
            conn.execute(
                """INSERT INTO email_threads (id, subject, customer_id, last_activity_iso, snippet)
                   VALUES (?, ?, ?, ?, ?)""",
                (tid, subject, None, now_iso, body[:60]),
            )
        else:
            conn.execute(
                "UPDATE email_threads SET last_activity_iso = ?, snippet = ? WHERE id = ?",
                (now_iso, body[:60], tid),
            )

        mid = f"EMAIL-{hashlib.md5(f'{now_iso}-{body}'.encode()).hexdigest()[:8]}"
        conn.execute(
            """INSERT INTO emails (id, thread_id, from_addr, to_addrs, cc_addrs, bcc_addrs, subject, body, date_iso, is_read, folder)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (mid, tid, actor, json.dumps(to_list), json.dumps(cc_list), json.dumps([]), subject, body, now_iso, 1, "sent"),
        )
        log_action(conn, clock, actor, "mail", "send_message", "email", mid, {"to": to_list, "cc": cc_list, "subject": subject, "thread_id": tid})
        return {"sent": True, "message_id": mid, "thread_id": tid, "timestamp_iso": now_iso}


# ===========================================================================
# 2. Calendar
# ===========================================================================

def cal_list_events(
    db_path: Path,
    start_iso: str | None = None,
    end_iso: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("calendar", "list_events")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        sql = "SELECT * FROM calendar_events WHERE 1=1"
        params: list[Any] = []
        if start_iso:
            sql += " AND start_iso >= ?"
            params.append(start_iso)
        if end_iso:
            sql += " AND end_iso <= ?"
            params.append(end_iso)
        sql += " ORDER BY start_iso ASC LIMIT 50"
        events = query_rows(conn, sql, tuple(params))
        for ev in events:
            ev["attendees"] = json.loads(ev["attendees"]) if ev.get("attendees") else []
        log_action(conn, clock, actor, "calendar", "list_events", "calendar", "default")
        return {"events": events, "count": len(events)}


def cal_create_event(
    db_path: Path,
    title: str,
    start_iso: str,
    end_iso: str,
    attendees: list[str] | str | None = None,
    description: str = "",
    location: str = "",
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("calendar", "create_event")
    att_list = ([attendees] if isinstance(attendees, str) else list(attendees)) if attendees else [actor]
    if actor not in att_list:
        att_list.append(actor)

    with connect(db_path) as conn:
        clock.advance(20, conn)
        event_id = f"CAL-{hashlib.md5(f'{title}-{start_iso}'.encode()).hexdigest()[:8]}"
        conn.execute(
            """INSERT INTO calendar_events (id, title, organizer_email, start_iso, end_iso, location, description, status, attendees)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event_id, title, actor, start_iso, end_iso, location, description, "confirmed", json.dumps(att_list)),
        )
        log_action(conn, clock, actor, "calendar", "create_event", "event", event_id, {"title": title, "start": start_iso, "end": end_iso, "attendees": att_list})
        return {"created": True, "event_id": event_id, "title": title, "start_iso": start_iso, "end_iso": end_iso}


# ===========================================================================
# 3. Drive & Filesystem
# ===========================================================================

def drive_list_files(
    db_path: Path,
    directory: str = "/",
    search: str = "",
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("drive", "list_files")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        sql = "SELECT id, name, virtual_path, mime_type, size_bytes, owner_email, customer_id, version, updated_iso FROM files WHERE 1=1"
        params: list[Any] = []
        if directory and directory != "/":
            sql += " AND virtual_path LIKE ?"
            params.append(f"{directory.rstrip('/')}/%")
        if search:
            sql += " AND (name LIKE ? OR virtual_path LIKE ? OR content_text LIKE ?)"
            s_like = f"%{search}%"
            params.extend([s_like, s_like, s_like])
        sql += " ORDER BY virtual_path ASC LIMIT 100"
        files = query_rows(conn, sql, tuple(params))
        log_action(conn, clock, actor, "drive", "list_files", "directory", directory, {"search": search})
        return {"files": files, "count": len(files)}


def drive_read_file(
    db_path: Path,
    file_path: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("drive", "read_file")
    with connect(db_path) as conn:
        clock.advance(15, conn)
        row = conn.execute("SELECT * FROM files WHERE virtual_path = ? OR id = ?", (file_path, file_path)).fetchone()
        if not row:
            raise ServiceError("not_found", f"File '{file_path}' not found in Drive.")
        data = dict(row)
        log_action(conn, clock, actor, "drive", "read_file", "file", data["id"], {"path": data["virtual_path"]})
        return data


def drive_write_file(
    db_path: Path,
    file_path: str,
    content: str,
    mime_type: str = "text/plain",
    customer_id: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("drive", "write_file")
    with connect(db_path) as conn:
        now_iso = clock.advance(25, conn)
        existing = conn.execute("SELECT id, version FROM files WHERE virtual_path = ?", (file_path,)).fetchone()
        name = file_path.rstrip("/").split("/")[-1]
        if existing:
            file_id = existing["id"]
            new_version = existing["version"] + 1
            conn.execute(
                """UPDATE files SET content_text = ?, size_bytes = ?, version = ?, updated_iso = ?
                   WHERE id = ?""",
                (content, len(content), new_version, now_iso, file_id),
            )
        else:
            file_id = f"FILE-{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
            conn.execute(
                """INSERT INTO files (id, name, virtual_path, mime_type, size_bytes, owner_email, customer_id, content_text, version, created_iso, updated_iso)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_id, name, file_path, mime_type, len(content), actor, customer_id, content, 1, now_iso, now_iso),
            )
        log_action(conn, clock, actor, "drive", "write_file", "file", file_id, {"path": file_path, "size": len(content)})
        return {"written": True, "file_id": file_id, "virtual_path": file_path, "size_bytes": len(content)}


# ===========================================================================
# 4. CRM System
# ===========================================================================

def crm_search_customers(
    db_path: Path,
    query: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("crm", "search_customers")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        sql = """
            SELECT id, name, domain, account_tier, status, phone, primary_contact_id, msa_date
            FROM customers
            WHERE name LIKE ? OR domain LIKE ? OR id = ?
            ORDER BY name ASC LIMIT 20
        """
        q_like = f"%{query}%"
        customers = query_rows(conn, sql, (q_like, q_like, query))
        log_action(conn, clock, actor, "crm", "search_customers", "query", query)
        return {"customers": customers, "count": len(customers)}


def crm_get_customer(
    db_path: Path,
    customer_id: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("crm", "get_customer")
    with connect(db_path) as conn:
        clock.advance(15, conn)
        cust = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not cust:
            raise ServiceError("not_found", f"Customer '{customer_id}' not found.")

        contacts = query_rows(conn, "SELECT * FROM crm_contacts WHERE customer_id = ?", (customer_id,))
        deals = query_rows(conn, "SELECT * FROM crm_deals WHERE customer_id = ?", (customer_id,))
        activity = query_rows(conn, "SELECT * FROM crm_activity_logs WHERE customer_id = ? ORDER BY created_ts DESC", (customer_id,))
        invoices = query_rows(conn, "SELECT id, invoice_number, amount_cents, status, issued_date, due_date FROM invoices WHERE customer_id = ?", (customer_id,))
        tickets = query_rows(conn, "SELECT id, subject, priority, status FROM tickets WHERE customer_id = ?", (customer_id,))

        log_action(conn, clock, actor, "crm", "get_customer", "customer", customer_id)
        return {
            "customer": dict(cust),
            "contacts": contacts,
            "deals": deals,
            "activity_logs": activity,
            "invoices": invoices,
            "tickets": tickets,
        }


def crm_update_customer(
    db_path: Path,
    customer_id: str,
    status: str | None = None,
    account_tier: str | None = None,
    phone: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("crm", "update_customer")
    with connect(db_path) as conn:
        clock.advance(20, conn)
        updates: list[str] = []
        params: list[Any] = []
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if account_tier is not None:
            updates.append("account_tier = ?")
            params.append(account_tier)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)

        if not updates:
            return {"updated": False, "message": "No updates specified"}

        params.append(customer_id)
        sql = f"UPDATE customers SET {', '.join(updates)} WHERE id = ?"
        conn.execute(sql, tuple(params))
        log_action(conn, clock, actor, "crm", "update_customer", "customer", customer_id, {"status": status, "tier": account_tier})
        return {"updated": True, "customer_id": customer_id, "status": status}


def crm_add_activity(
    db_path: Path,
    customer_id: str,
    activity_type: str,
    body: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("crm", "add_activity")
    with connect(db_path) as conn:
        now_iso = clock.advance(15, conn)
        act_id = f"ACT-{hashlib.md5(f'{now_iso}-{body}'.encode()).hexdigest()[:8]}"
        conn.execute(
            """INSERT INTO crm_activity_logs (id, customer_id, author_id, activity_type, body, created_ts)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (act_id, customer_id, actor, activity_type, body, now_iso),
        )
        log_action(conn, clock, actor, "crm", "add_activity", "activity", act_id, {"customer_id": customer_id, "type": activity_type, "body": body})
        return {"created": True, "activity_id": act_id, "created_ts": now_iso}


# ===========================================================================
# 5. Billing & Invoicing
# ===========================================================================

def billing_get_invoice(
    db_path: Path,
    invoice_number: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("billing", "get_invoice")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        inv = conn.execute("SELECT * FROM invoices WHERE invoice_number = ? OR id = ?", (invoice_number, invoice_number)).fetchone()
        if not inv:
            raise ServiceError("not_found", f"Invoice '{invoice_number}' not found.")
        data = dict(inv)
        data["items"] = json.loads(data["items"]) if data.get("items") else []
        refunds = query_rows(conn, "SELECT * FROM refunds WHERE invoice_id = ?", (data["id"],))
        data["refunds"] = refunds
        log_action(conn, clock, actor, "billing", "get_invoice", "invoice", data["id"])
        return data


def billing_calculate_refund(
    db_path: Path,
    invoice_number: str,
    notice_date_iso: str = "2026-10-14T09:00:00Z",
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    """Calculate pro-rated refund amount per Section 4.2 / SOP-OPS-042:

    Annual contract (365 days).
    Notice date: October 14, 2026.
    Issued/Paid date: August 15, 2026 (60 elapsed days).
    Unexpired days = 365 - 60 = 305 days.
    Base pro-rata = (Amount * 305) / 365.
    10% administrative processing fee subtracted.
    """
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("billing", "calculate_refund")
    with connect(db_path) as conn:
        clock.advance(15, conn)
        inv = conn.execute("SELECT * FROM invoices WHERE invoice_number = ? OR id = ?", (invoice_number, invoice_number)).fetchone()
        if not inv:
            raise ServiceError("not_found", f"Invoice '{invoice_number}' not found.")

        issued_dt = datetime.date.fromisoformat(inv["issued_date"][:10])
        notice_dt = datetime.date.fromisoformat(notice_date_iso[:10])
        elapsed_days = (notice_dt - issued_dt).days
        total_term_days = 365
        unexpired_days = max(0, total_term_days - elapsed_days)

        amount_cents = inv["amount_cents"]
        base_pro_rata = (amount_cents * unexpired_days) / total_term_days
        admin_fee_cents = round(base_pro_rata * 0.10)
        net_refund_cents = round(base_pro_rata - admin_fee_cents)

        res = {
            "invoice_number": inv["invoice_number"],
            "invoice_amount_cents": amount_cents,
            "issued_date": inv["issued_date"],
            "notice_date": notice_date_iso[:10],
            "elapsed_days": elapsed_days,
            "unexpired_days": unexpired_days,
            "base_pro_rata_cents": round(base_pro_rata),
            "admin_fee_cents": admin_fee_cents,
            "allowed_refund_cents": net_refund_cents,
            "formula": "net_refund = (invoice_amount * unexpired_days / 365) * 0.90",
        }
        log_action(conn, clock, actor, "billing", "calculate_refund", "invoice", inv["id"], res)
        return res


def billing_issue_refund(
    db_path: Path,
    invoice_number: str,
    amount_cents: int,
    reason: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("billing", "issue_refund")
    with connect(db_path) as conn:
        now_iso = clock.advance(30, conn)
        inv = conn.execute("SELECT * FROM invoices WHERE invoice_number = ? OR id = ?", (invoice_number, invoice_number)).fetchone()
        if not inv:
            raise ServiceError("not_found", f"Invoice '{invoice_number}' not found.")

        inv_id = inv["id"]
        ref_id = f"REF-{hashlib.md5(f'{inv_id}-{amount_cents}-{now_iso}'.encode()).hexdigest()[:8]}"
        conn.execute(
            """INSERT OR REPLACE INTO refunds (id, invoice_id, customer_id, amount_cents, reason, status, processed_by, created_iso)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (ref_id, inv["id"], inv["customer_id"], amount_cents, reason, "completed", actor, now_iso),
        )
        conn.execute("UPDATE invoices SET status = 'refunded' WHERE id = ?", (inv["id"],))
        log_action(conn, clock, actor, "billing", "issue_refund", "refund", ref_id, {"invoice_id": inv["id"], "amount_cents": amount_cents, "reason": reason})
        return {"refunded": True, "refund_id": ref_id, "invoice_number": inv["invoice_number"], "amount_cents": amount_cents, "status": "completed"}


# ===========================================================================
# 6. Support Tickets
# ===========================================================================

def tickets_list(
    db_path: Path,
    status: str | None = None,
    customer_id: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("tickets", "list_tickets")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        sql = "SELECT id, customer_id, requester_email, assignee_id, subject, priority, status, updated_iso FROM tickets WHERE 1=1"
        params: list[Any] = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if customer_id:
            sql += " AND customer_id = ?"
            params.append(customer_id)
        sql += " ORDER BY updated_iso DESC LIMIT 50"
        tickets = query_rows(conn, sql, tuple(params))
        log_action(conn, clock, actor, "tickets", "list_tickets", "filter", status or "all")
        return {"tickets": tickets, "count": len(tickets)}


def tickets_get(
    db_path: Path,
    ticket_id: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("tickets", "get_ticket")
    with connect(db_path) as conn:
        clock.advance(15, conn)
        tick = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not tick:
            raise ServiceError("not_found", f"Ticket '{ticket_id}' not found.")
        comments = query_rows(conn, "SELECT * FROM ticket_comments WHERE ticket_id = ? ORDER BY created_iso ASC", (ticket_id,))
        log_action(conn, clock, actor, "tickets", "get_ticket", "ticket", ticket_id)
        return {"ticket": dict(tick), "comments": comments}


def tickets_update(
    db_path: Path,
    ticket_id: str,
    status: str | None = None,
    priority: str | None = None,
    comment: str | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("tickets", "update_ticket")
    with connect(db_path) as conn:
        now_iso = clock.advance(20, conn)
        updates = ["updated_iso = ?"]
        params: list[Any] = [now_iso]
        if status:
            updates.append("status = ?")
            params.append(status)
        if priority:
            updates.append("priority = ?")
            params.append(priority)
        params.append(ticket_id)
        conn.execute(f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?", tuple(params))

        if comment:
            cid = f"COMM-{hashlib.md5(f'{ticket_id}-{now_iso}'.encode()).hexdigest()[:8]}"
            conn.execute(
                """INSERT INTO ticket_comments (id, ticket_id, author_email, body, is_internal, created_iso)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cid, ticket_id, actor, comment, 0, now_iso),
            )
        log_action(conn, clock, actor, "tickets", "update_ticket", "ticket", ticket_id, {"status": status, "comment": comment})
        return {"updated": True, "ticket_id": ticket_id, "status": status}


# ===========================================================================
# 7. Knowledge Base
# ===========================================================================

def kb_search(
    db_path: Path,
    query: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("kb", "search")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        sql = "SELECT id, category, title, tags, updated_iso FROM kb_articles WHERE title LIKE ? OR body LIKE ? OR tags LIKE ?"
        q_like = f"%{query}%"
        articles = query_rows(conn, sql, (q_like, q_like, q_like))
        log_action(conn, clock, actor, "kb", "search", "query", query)
        return {"articles": articles, "count": len(articles)}


def kb_get_article(
    db_path: Path,
    article_id: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("kb", "get_article")
    with connect(db_path) as conn:
        clock.advance(15, conn)
        art = conn.execute("SELECT * FROM kb_articles WHERE id = ?", (article_id,)).fetchone()
        if not art:
            raise ServiceError("not_found", f"Article '{article_id}' not found.")
        log_action(conn, clock, actor, "kb", "get_article", "article", article_id)
        return dict(art)


# ===========================================================================
# 8. Terminal / Shell Simulation
# ===========================================================================

def terminal_execute(
    db_path: Path,
    command: str,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    clock, disturbances = _get_clock_and_disturbances(db_path)
    disturbances.evaluate_action("terminal", "execute")
    with connect(db_path) as conn:
        clock.advance(10, conn)
        cmd = command.strip()
        stdout = ""
        stderr = ""
        exit_code = 0

        if cmd.startswith("whoami"):
            stdout = actor.split("@")[0]
        elif cmd.startswith("date"):
            stdout = clock.get_time_iso(conn)
        elif cmd.startswith("hostname"):
            stdout = "apex-workstation-ops01"
        elif cmd.startswith("uptime"):
            stdout = "up 14 days, 3:42, 1 user, load average: 0.12, 0.08, 0.05"
        elif cmd.startswith("ls"):
            stdout = "Desktop  Documents  Downloads  Drive  Applications"
        elif cmd.startswith("help"):
            stdout = "Available simulated commands: whoami, date, hostname, uptime, ls, echo, cat, ping, curl"
        else:
            stdout = f"Command executed: {cmd}"

        log_action(conn, clock, actor, "terminal", "execute", "command", cmd)
        return {"command": cmd, "stdout": stdout, "stderr": stderr, "exit_code": exit_code}


def _resolve_arg(args: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Extract argument trying multiple aliases and casing conventions."""
    for k in keys:
        if k in args and args[k] is not None:
            return args[k]
        camel = "".join(w.capitalize() if i > 0 else w for i, w in enumerate(k.split("_")))
        if camel in args and args[camel] is not None:
            return args[camel]
    return default


def workstation_get_audit_events(
    db_path: Path,
    limit: int = 50,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    """Retrieve recent action logs from the authoritative append-only audit trail."""
    with connect(db_path) as conn:
        rows = query_rows(conn, "SELECT * FROM action_logs ORDER BY id DESC LIMIT ?", (limit,))
        parsed_rows = []
        for r in reversed(rows):
            item = dict(r)
            if "payload_json" in item and item["payload_json"]:
                try:
                    item["payload"] = json.loads(item["payload_json"])
                except Exception:
                    item["payload"] = {}
            parsed_rows.append(item)
        return {"events": parsed_rows, "count": len(parsed_rows)}


def workstation_step_simulation(
    db_path: Path,
    seconds: int = 60,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    """Advance the workstation virtual clock deterministically."""
    clock, _ = _get_clock_and_disturbances(db_path)
    with connect(db_path) as conn:
        new_ts = clock.advance(seconds, conn)
        log_action(conn, clock, actor, "simulation", "step", "time", f"+{seconds}s", {"new_time_iso": new_ts})
        return {"stepped_seconds": seconds, "current_time_iso": new_ts}


def workstation_submit_task(
    db_path: Path,
    summary: str,
    affected_ids: list[str] | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    """Formal completion submission for the workstation benchmark episode."""
    clock, _ = _get_clock_and_disturbances(db_path)
    with connect(db_path) as conn:
        log_action(
            conn, clock, actor, "task", "submit", "task_completion", summary,
            {"summary": summary, "affected_ids": affected_ids or []}
        )
        return {
            "submitted": True,
            "summary": summary,
            "affected_ids": affected_ids or [],
            "timestamp_iso": clock.get_time_iso(conn),
        }


# ===========================================================================
# Universal Dispatcher & State Verification
# ===========================================================================

TOOL_HANDLERS = {
    "mail_list_threads": lambda db, args, actor: mail_list_threads(
        db, _resolve_arg(args, "folder", default="inbox"), _resolve_arg(args, "query", "q", default=""), actor
    ),
    "mail_get_thread": lambda db, args, actor: mail_get_thread(
        db, _resolve_arg(args, "thread_id", "threadId", "id"), actor
    ),
    "mail_send_message": lambda db, args, actor: mail_send_message(
        db,
        _resolve_arg(args, "to", "recipients"),
        _resolve_arg(args, "subject"),
        _resolve_arg(args, "body", "text", "content"),
        _resolve_arg(args, "cc", default=None),
        _resolve_arg(args, "thread_id", "threadId", default=None),
        actor,
    ),
    "cal_list_events": lambda db, args, actor: cal_list_events(
        db, _resolve_arg(args, "start_iso", "startIso", "start"), _resolve_arg(args, "end_iso", "endIso", "end"), actor
    ),
    "cal_create_event": lambda db, args, actor: cal_create_event(
        db,
        _resolve_arg(args, "title"),
        _resolve_arg(args, "start_iso", "startIso"),
        _resolve_arg(args, "end_iso", "endIso"),
        _resolve_arg(args, "attendees", default=None),
        _resolve_arg(args, "description", default=""),
        _resolve_arg(args, "location", default=""),
        actor,
    ),
    "drive_list_files": lambda db, args, actor: drive_list_files(
        db, _resolve_arg(args, "directory", "dir", default="/"), _resolve_arg(args, "search", "q", default=""), actor
    ),
    "drive_read_file": lambda db, args, actor: drive_read_file(
        db, _resolve_arg(args, "file_path", "filePath", "path"), actor
    ),
    "drive_write_file": lambda db, args, actor: drive_write_file(
        db,
        _resolve_arg(args, "file_path", "filePath", "path"),
        _resolve_arg(args, "content", "text"),
        _resolve_arg(args, "mime_type", "mimeType", default="text/plain"),
        _resolve_arg(args, "customer_id", "customerId", default=None),
        actor,
    ),
    "crm_search_customers": lambda db, args, actor: crm_search_customers(
        db, _resolve_arg(args, "query", "q"), actor
    ),
    "crm_get_customer": lambda db, args, actor: crm_get_customer(
        db, _resolve_arg(args, "customer_id", "customerId", "id"), actor
    ),
    "crm_update_customer": lambda db, args, actor: crm_update_customer(
        db,
        _resolve_arg(args, "customer_id", "customerId", "id"),
        _resolve_arg(args, "status", default=None),
        _resolve_arg(args, "account_tier", "accountTier", default=None),
        _resolve_arg(args, "phone", default=None),
        actor,
    ),
    "crm_add_activity": lambda db, args, actor: crm_add_activity(
        db,
        _resolve_arg(args, "customer_id", "customerId", "id"),
        _resolve_arg(args, "activity_type", "activityType", "type"),
        _resolve_arg(args, "body", "note", "content"),
        actor,
    ),
    "billing_get_invoice": lambda db, args, actor: billing_get_invoice(
        db, _resolve_arg(args, "invoice_number", "invoiceNumber", "id"), actor
    ),
    "billing_calculate_refund": lambda db, args, actor: billing_calculate_refund(
        db,
        _resolve_arg(args, "invoice_number", "invoiceNumber", "id"),
        _resolve_arg(args, "notice_date_iso", "noticeDateIso", default="2026-10-14T09:00:00Z"),
        actor,
    ),
    "billing_issue_refund": lambda db, args, actor: billing_issue_refund(
        db,
        _resolve_arg(args, "invoice_number", "invoiceNumber", "id"),
        _resolve_arg(args, "amount_cents", "amountCents"),
        _resolve_arg(args, "reason"),
        actor,
    ),
    "tickets_list": lambda db, args, actor: tickets_list(
        db, _resolve_arg(args, "status", default=None), _resolve_arg(args, "customer_id", "customerId", default=None), actor
    ),
    "tickets_get": lambda db, args, actor: tickets_get(
        db, _resolve_arg(args, "ticket_id", "ticketId", "id"), actor
    ),
    "tickets_update": lambda db, args, actor: tickets_update(
        db,
        _resolve_arg(args, "ticket_id", "ticketId", "id"),
        _resolve_arg(args, "status", default=None),
        _resolve_arg(args, "priority", default=None),
        _resolve_arg(args, "comment", "notes", default=None),
        actor,
    ),
    "kb_search": lambda db, args, actor: kb_search(
        db, _resolve_arg(args, "query", "q"), actor
    ),
    "kb_get_article": lambda db, args, actor: kb_get_article(
        db, _resolve_arg(args, "article_id", "articleId", "id"), actor
    ),
    "terminal_execute": lambda db, args, actor: terminal_execute(
        db, _resolve_arg(args, "command", "cmd"), actor
    ),
    # Core Standard Primitives & Aliases
    "workstation_get_audit_events": lambda db, args, actor: workstation_get_audit_events(
        db, int(_resolve_arg(args, "limit", default=50)), actor
    ),
    "get_audit_events": lambda db, args, actor: workstation_get_audit_events(
        db, int(_resolve_arg(args, "limit", default=50)), actor
    ),
    "workstation_step_simulation": lambda db, args, actor: workstation_step_simulation(
        db, int(_resolve_arg(args, "seconds", "secs", default=60)), actor
    ),
    "step_simulation": lambda db, args, actor: workstation_step_simulation(
        db, int(_resolve_arg(args, "seconds", "secs", default=60)), actor
    ),
    "workstation_submit_task": lambda db, args, actor: workstation_submit_task(
        db,
        _resolve_arg(args, "summary", default="Task completed"),
        _resolve_arg(args, "affected_ids", "affectedIds", default=None),
        actor,
    ),
    "submit_task": lambda db, args, actor: workstation_submit_task(
        db,
        _resolve_arg(args, "summary", default="Task completed"),
        _resolve_arg(args, "affected_ids", "affectedIds", default=None),
        actor,
    ),
}



def execute_tool(
    db_path: Path | str,
    tool_name: str,
    arguments: dict[str, Any],
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    """Execute a workstation tool by name against the canonical SQLite database."""
    db_path = Path(db_path)
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        raise ServiceError("unknown_tool", f"Tool '{tool_name}' is not recognized.")
    return handler(db_path, arguments, actor)


def export_state(db_path: Path | str) -> dict[str, Any]:
    """Export complete canonical relational state as JSON."""
    db_path = Path(db_path)
    with connect(db_path) as conn:
        tables = [
            "system_state", "employees", "customers", "crm_contacts", "crm_deals",
            "crm_activity_logs", "email_threads", "emails", "calendar_events",
            "files", "tickets", "ticket_comments", "invoices", "refunds",
            "kb_articles", "action_logs"
        ]
        result: dict[str, Any] = {}
        for tbl in tables:
            rows = query_rows(conn, f"SELECT * FROM {tbl} ORDER BY 1 ASC")
            result[tbl] = rows
        return result


def calculate_state_hash(db_path: Path | str) -> str:
    """Compute SHA-256 hash over canonical database state to confirm determinism."""
    state = export_state(db_path)
    # Exclude dynamic action logs and virtual ticks when checking seed reproducibility
    reproducible_state = {k: v for k, v in state.items() if k not in ("action_logs",)}
    canonical_json = json.dumps(reproducible_state, sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
