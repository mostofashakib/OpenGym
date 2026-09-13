"""Universal enterprise service layer orchestrating all 11 simulators, workflows, and policies."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from .db_generator import calculate_database_hash
from .policy_engine import EnterprisePolicyEngine, PolicyViolation
from .workflow_engine import WorkflowEngine


class HealthcareService:
    pass


class EnterpriseService:
    """Operations service layer connecting 11 enterprise systems through a shared organization model."""

    def __init__(
        self,
        db_path: Any,
        actor_id: str = "emp-003",
        actor_role_id: str = "role-mgr-supp",
    ) -> None:
        if hasattr(db_path, "db_path"):
            self.db_path = Path(db_path.db_path)
        else:
            self.db_path = Path(db_path)
        self.actor_id = actor_id
        self.actor_role_id = actor_role_id

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _log_audit(
        self,
        conn: sqlite3.Connection,
        action: str,
        resource_type: str,
        resource_id: str,
        authorized: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an immutable audit event."""
        time_iso = "2026-10-15T09:00:00Z"
        conn.execute(
            """INSERT INTO audit_events (
                timestamp_iso, actor_id, actor_role, action, resource_type, resource_id, authorized, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time_iso,
                self.actor_id,
                self.actor_role_id,
                action,
                resource_type,
                resource_id,
                1 if authorized else 0,
                json.dumps(details or {}),
            ),
        )

    # 1. Organization Directory
    def search_organization(
        self, query: Optional[str] = None, department_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            sql = """
                SELECT e.id, e.first_name, e.last_name, e.email, e.title, d.name as department, t.name as team, e.manager_id, r.id as role_id, r.approval_limit_usd
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                JOIN teams t ON e.team_id = t.id
                JOIN roles r ON e.role_id = r.id
                WHERE 1=1
            """
            params: List[Any] = []
            if query:
                sql += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.email LIKE ? OR e.title LIKE ?)"
                like = f"%{query}%"
                params.extend([like, like, like, like])
            if department_code:
                sql += " AND d.code = ?"
                params.append(department_code)

            sql += " ORDER BY e.id ASC"
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """SELECT e.*, d.name as department_name, r.title as role_title, r.approval_limit_usd
                   FROM employees e
                   JOIN departments d ON e.department_id = d.id
                   JOIN roles r ON e.role_id = r.id
                   WHERE e.id = ?""",
                (employee_id,),
            ).fetchone()
            return dict(row) if row else None

    # 2. Customer 360 View
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            cust = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
            if not cust:
                return {"error": f"Customer {customer_id} not found."}

            contacts = conn.execute("SELECT * FROM contacts WHERE customer_id = ?", (customer_id,)).fetchall()
            contracts = conn.execute("SELECT * FROM contracts WHERE customer_id = ?", (customer_id,)).fetchall()
            invoices = conn.execute("SELECT * FROM invoices WHERE customer_id = ? ORDER BY due_date DESC LIMIT 5", (customer_id,)).fetchall()
            tickets = conn.execute("SELECT * FROM support_tickets WHERE customer_id = ? ORDER BY created_iso DESC LIMIT 5", (customer_id,)).fetchall()
            deals = conn.execute("SELECT * FROM crm_deals WHERE customer_id = ?", (customer_id,)).fetchall()

            self._log_audit(conn, "read", "Customer", customer_id, details={"action": "view_customer_360"})
            conn.commit()

            return {
                "customer": dict(cust),
                "contacts": [dict(c) for c in contacts],
                "contracts": [dict(c) for c in contracts],
                "invoices": [dict(i) for i in invoices],
                "tickets": [dict(t) for t in tickets],
                "deals": [dict(d) for d in deals],
            }

    # 3. CRM Operations
    def crm_query_records(self, record_type: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            table = "crm_deals" if record_type == "deals" else ("crm_leads" if record_type == "leads" else "customers")
            rows = conn.execute(f"SELECT * FROM {table} LIMIT 25").fetchall()
            return [dict(r) for r in rows]

    def crm_update_deal(self, deal_id: str, stage: str, notes: str = "") -> Dict[str, Any]:
        with self._connect() as conn:
            conn.execute("UPDATE crm_deals SET stage = ? WHERE id = ?", (stage, deal_id))
            self._log_audit(conn, "update", "CRMDeal", deal_id, details={"stage": stage, "notes": notes})
            conn.commit()
            return {"success": True, "deal_id": deal_id, "stage": stage}

    # 4. Support Ticket Operations
    def support_get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            tkt = conn.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,)).fetchone()
            if not tkt:
                return {"error": f"Ticket {ticket_id} not found."}

            comments = conn.execute(
                "SELECT * FROM ticket_comments WHERE ticket_id = ? ORDER BY created_iso ASC", (ticket_id,)
            ).fetchall()

            self._log_audit(conn, "read", "SupportTicket", ticket_id)
            conn.commit()

            return {
                "ticket": dict(tkt),
                "comments": [dict(c) for c in comments],
            }

    def support_add_comment(self, ticket_id: str, content: str, is_internal: bool = False) -> Dict[str, Any]:
        with self._connect() as conn:
            # DLP Scan
            dlp_violation = EnterprisePolicyEngine.check_data_loss_prevention(content, context_label=f"ticket_{ticket_id}")
            if dlp_violation:
                self._log_audit(conn, "dlp_violation", "SupportTicket", ticket_id, authorized=False, details={"error": dlp_violation.description})
                conn.commit()
                return {"success": False, "policy_violation": dlp_violation.description}

            comm_id = f"comm-{ticket_id}-{len(conn.execute('SELECT id FROM ticket_comments').fetchall()) + 1:04d}"
            conn.execute(
                """INSERT INTO ticket_comments (id, ticket_id, author_id, is_internal, content, created_iso)
                   VALUES (?, ?, ?, ?, ?, '2026-10-15T09:30:00Z')""",
                (comm_id, ticket_id, self.actor_id, 1 if is_internal else 0, content),
            )
            self._log_audit(conn, "comment", "SupportTicket", ticket_id, details={"comment_id": comm_id, "is_internal": is_internal})
            conn.commit()
            return {"success": True, "comment_id": comm_id, "ticket_id": ticket_id}

    def support_update_ticket_status(self, ticket_id: str, status: str) -> Dict[str, Any]:
        with self._connect() as conn:
            resolved_iso = "2026-10-15T10:30:00Z" if status in ("resolved", "closed") else None
            conn.execute(
                "UPDATE support_tickets SET status = ?, resolved_iso = ? WHERE id = ?",
                (status, resolved_iso, ticket_id),
            )
            self._log_audit(conn, "update_status", "SupportTicket", ticket_id, details={"status": status})
            conn.commit()
            return {"success": True, "ticket_id": ticket_id, "status": status}

    # 5. Billing & Refunds
    def billing_get_invoices(self, customer_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM invoices WHERE customer_id = ?", (customer_id,)).fetchall()
            return [dict(r) for r in rows]

    def billing_process_refund(
        self,
        invoice_id: str,
        customer_id: str,
        amount_usd: float,
        reason: str,
        approved_by_id: Optional[str] = None,
        workflow_instance_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issue a refund while strictly validating financial authorization and contract caps."""
        with self._connect() as conn:
            # 1. Check Financial Authorization Policy
            auth_violation = EnterprisePolicyEngine.check_financial_authorization(
                self.actor_id, self.actor_role_id, amount_usd, approved_by_id, conn
            )
            if auth_violation:
                self._log_audit(conn, "policy_violation", "BillingRefund", invoice_id, authorized=False, details={"error": auth_violation.description})
                conn.commit()
                return {"success": False, "policy_violation": auth_violation.description}

            # 2. Check SLA Contract Concession Cap
            sla_violation = EnterprisePolicyEngine.check_contract_concession_cap(customer_id, amount_usd, conn)
            if sla_violation:
                self._log_audit(conn, "policy_violation", "BillingRefund", invoice_id, authorized=False, details={"error": sla_violation.description})
                conn.commit()
                return {"success": False, "policy_violation": sla_violation.description}

            ref_id = f"ref-{invoice_id}-{len(conn.execute('SELECT id FROM refund_records').fetchall()) + 1:04d}"
            conn.execute(
                """INSERT INTO refund_records (
                    id, invoice_id, customer_id, amount_usd, reason, requested_by_id, approved_by_id, status, created_iso, processed_iso
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'processed', '2026-10-15T09:30:00Z', '2026-10-15T09:30:00Z')""",
                (ref_id, invoice_id, customer_id, amount_usd, reason, self.actor_id, approved_by_id),
            )

            # Advance workflow if associated
            if workflow_instance_id:
                engine = WorkflowEngine(conn)
                engine.advance_step(workflow_instance_id, "refund_processed", {"refund_id": ref_id, "amount_usd": amount_usd})

            self._log_audit(conn, "process_refund", "RefundRecord", ref_id, details={"amount_usd": amount_usd, "invoice_id": invoice_id})
            conn.commit()

            return {
                "success": True,
                "refund_id": ref_id,
                "invoice_id": invoice_id,
                "customer_id": customer_id,
                "amount_usd": amount_usd,
                "status": "processed",
            }

    # 6. Email Operations
    def email_read_inbox(self, user_email: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM email_messages WHERE recipient_emails_json LIKE ? ORDER BY sent_iso DESC LIMIT ?",
                (f"%{user_email}%", limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def email_send_message(
        self,
        sender_email: str,
        recipient_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            # DLP Scan
            dlp_violation = EnterprisePolicyEngine.check_data_loss_prevention(body, context_label="email_outbound")
            if dlp_violation:
                self._log_audit(conn, "dlp_violation", "EmailMessage", "outbound", authorized=False, details={"error": dlp_violation.description})
                conn.commit()
                return {"success": False, "policy_violation": dlp_violation.description}

            email_id = f"email-{len(conn.execute('SELECT id FROM email_messages').fetchall()) + 1:04d}"
            thread_id = f"th-{email_id}"
            conn.execute(
                """INSERT INTO email_messages (
                    id, sender_email, recipient_emails_json, cc_emails_json, subject, body, sent_iso, thread_id, is_read, folder
                ) VALUES (?, ?, ?, ?, ?, ?, '2026-10-15T09:30:00Z', ?, 1, 'sent')""",
                (email_id, sender_email, json.dumps(recipient_emails), json.dumps(cc_emails or []), subject, body, thread_id),
            )
            self._log_audit(conn, "send_email", "EmailMessage", email_id, details={"recipients": recipient_emails, "subject": subject})
            conn.commit()
            return {"success": True, "email_id": email_id, "recipients": recipient_emails}

    # 7. Manager Approvals & Escalations
    def workflow_request_approval(
        self,
        request_type: str,
        approver_id: str,
        amount_usd: float,
        reason: str,
        workflow_instance_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            # Segregation of duties check
            sod = EnterprisePolicyEngine.check_segregation_of_duties(self.actor_id, approver_id)
            if sod:
                self._log_audit(conn, "policy_violation", "ApprovalRequest", "new", authorized=False, details={"error": sod.description})
                conn.commit()
                return {"success": False, "policy_violation": sod.description}

            req_id = f"appr-{len(conn.execute('SELECT id FROM approval_requests').fetchall()) + 1:04d}"
            conn.execute(
                """INSERT INTO approval_requests (
                    id, workflow_instance_id, request_type, requester_id, approver_id, amount_usd, reason, status, created_iso
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', '2026-10-15T09:15:00Z')""",
                (req_id, workflow_instance_id, request_type, self.actor_id, approver_id, amount_usd, reason),
            )

            if workflow_instance_id:
                engine = WorkflowEngine(conn)
                engine.block_for_approval(workflow_instance_id, req_id)

            self._log_audit(conn, "request_approval", "ApprovalRequest", req_id, details={"approver_id": approver_id, "amount_usd": amount_usd})
            conn.commit()
            return {"success": True, "approval_request_id": req_id, "status": "pending", "approver_id": approver_id}

    def list_customers(self, query: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if query:
                like = f"%{query}%"
                rows = conn.execute(
                    "SELECT * FROM customers WHERE company_name LIKE ? OR tier LIKE ? LIMIT ?",
                    (like, like, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM customers ORDER BY company_name ASC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_support_tickets(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT t.*, c.company_name as customer_name FROM support_tickets t JOIN customers c ON t.customer_id = c.id WHERE t.status = ? ORDER BY t.created_iso DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT t.*, c.company_name as customer_name FROM support_tickets t JOIN customers c ON t.customer_id = c.id ORDER BY t.created_iso DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def list_approval_requests(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    """SELECT a.*, e1.first_name || ' ' || e1.last_name as requester_name, e2.first_name || ' ' || e2.last_name as approver_name
                       FROM approval_requests a
                       JOIN employees e1 ON a.requester_id = e1.id
                       JOIN employees e2 ON a.approver_id = e2.id
                       WHERE a.status = ?
                       ORDER BY a.created_iso DESC LIMIT ?""",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT a.*, e1.first_name || ' ' || e1.last_name as requester_name, e2.first_name || ' ' || e2.last_name as approver_name
                       FROM approval_requests a
                       JOIN employees e1 ON a.requester_id = e1.id
                       JOIN employees e2 ON a.approver_id = e2.id
                       ORDER BY a.created_iso DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def decide_approval_request(
        self, request_id: str, decision: str, notes: str = ""
    ) -> Dict[str, Any]:
        """Record manager decision (approved/rejected) on an approval request."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,)).fetchone()
            if not row:
                return {"success": False, "error": f"Approval request {request_id} not found."}
            status = "approved" if decision.lower() in ("approved", "approve") else "rejected"
            decided_iso = "2026-10-15T09:45:00Z"
            conn.execute(
                """UPDATE approval_requests
                   SET status = ?, decision_notes = ?, decided_iso = ?
                   WHERE id = ?""",
                (status, notes, decided_iso, request_id),
            )
            wf_id = row["workflow_instance_id"]
            if wf_id and status == "approved":
                engine = WorkflowEngine(conn)
                engine.advance_step(wf_id, "approval_granted", {"approved_by": self.actor_id, "request_id": request_id})
            elif wf_id and status == "rejected":
                engine = WorkflowEngine(conn)
                engine.fail_workflow(wf_id, f"Approval rejected: {notes}")

            self._log_audit(conn, f"decision_{status}", "ApprovalRequest", request_id, details={"decision": status, "notes": notes})
            conn.commit()
            return {"success": True, "request_id": request_id, "status": status}

    def workflow_get_approval_status(self, request_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM approval_requests WHERE id = ?", (request_id,)).fetchone()
            if not row:
                return {"error": f"Approval request {request_id} not found."}
            return dict(row)

    # 8. Document Operations
    def document_read(self, document_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
            if not row:
                return {"error": f"Document {document_id} not found."}
            self._log_audit(conn, "read", "Document", document_id)
            conn.commit()
            return dict(row)

    # 9. Audit Log & State Hashing
    def get_audit_log(
        self, actor_id: Optional[str] = None, action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            sql = "SELECT * FROM audit_events WHERE 1=1"
            params: List[Any] = []
            if actor_id:
                sql += " AND actor_id = ?"
                params.append(actor_id)
            if action:
                sql += " AND action = ?"
                params.append(action)
            sql += " ORDER BY id ASC"
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def calculate_state_hash(self) -> str:
        return calculate_database_hash(self.db_path)

    def step_simulation(self, minutes: int = 15) -> Dict[str, Any]:
        """Advance virtual time and process any scheduled triggers."""
        from .event_scheduler import EventScheduler
        with self._connect() as conn:
            scheduler = EventScheduler(conn)
            new_time = scheduler.advance_virtual_time(minutes=minutes)
            self._log_audit(conn, "step_simulation", "VirtualClock", "clock", details={"advanced_minutes": minutes, "new_time": new_time})
            conn.commit()
        return {"stepped_minutes": minutes, "current_virtual_time": new_time}

    def submit_task(self, summary: str, affected_ids: str = "") -> Dict[str, Any]:
        """Submit formal completion report for the enterprise workflow episode."""
        parsed_ids = [i.strip() for i in affected_ids.split(",") if i.strip()] if affected_ids else []
        with self._connect() as conn:
            self._log_audit(conn, "submit_task", "Task", "task_completion", details={"summary": summary, "affected_ids": parsed_ids})
            conn.commit()
        return {"submitted": True, "summary": summary, "affected_ids": parsed_ids, "status": "completed"}
