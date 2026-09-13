"""Client interface for interacting with the Workstation environment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from workstation_sim.context import WorkstationContext
from workstation_sim.service import DEFAULT_ACTOR, execute_tool, export_state


class WorkstationClient:
    """High-level client for executing workstation actions and inspecting state."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        actor: str = DEFAULT_ACTOR,
    ) -> None:
        if db_path is not None:
            self.context = WorkstationContext(db_path=Path(db_path), actor=actor)
        else:
            self.context = WorkstationContext.from_env()
        self.context.ensure_initialized()

    def execute(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a tool on the workstation."""
        return self.context.execute_tool(tool_name, arguments or {})

    # Convenience helper methods
    def list_emails(self, folder: str = "inbox", query: str = "") -> dict[str, Any]:
        return self.execute("mail_list_threads", {"folder": folder, "query": query})

    def get_thread(self, thread_id: str) -> dict[str, Any]:
        return self.execute("mail_get_thread", {"thread_id": thread_id})

    def send_email(
        self,
        to: list[str] | str,
        subject: str,
        body: str,
        cc: list[str] | str | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        return self.execute("mail_send_message", {
            "to": [to] if isinstance(to, str) else list(to),
            "subject": subject,
            "body": body,
            "cc": ([cc] if isinstance(cc, str) else list(cc)) if cc else [],
            "thread_id": thread_id,
        })

    def list_events(self, start_iso: str | None = None, end_iso: str | None = None) -> dict[str, Any]:
        return self.execute("cal_list_events", {"start_iso": start_iso, "end_iso": end_iso})

    def create_event(
        self,
        title: str,
        start_iso: str,
        end_iso: str,
        attendees: list[str] | None = None,
        description: str = "",
        location: str = "",
    ) -> dict[str, Any]:
        return self.execute("cal_create_event", {
            "title": title,
            "start_iso": start_iso,
            "end_iso": end_iso,
            "attendees": attendees or [],
            "description": description,
            "location": location,
        })

    def list_files(self, directory: str = "/", search: str = "") -> dict[str, Any]:
        return self.execute("drive_list_files", {"directory": directory, "search": search})

    def read_file(self, file_path: str) -> dict[str, Any]:
        return self.execute("drive_read_file", {"file_path": file_path})

    def write_file(self, file_path: str, content: str, mime_type: str = "text/plain") -> dict[str, Any]:
        return self.execute("drive_write_file", {"file_path": file_path, "content": content, "mime_type": mime_type})

    def search_customers(self, query: str) -> dict[str, Any]:
        return self.execute("crm_search_customers", {"query": query})

    def get_customer(self, customer_id: str) -> dict[str, Any]:
        return self.execute("crm_get_customer", {"customer_id": customer_id})

    def update_customer(self, customer_id: str, status: str | None = None, tier: str | None = None) -> dict[str, Any]:
        return self.execute("crm_update_customer", {"customer_id": customer_id, "status": status, "account_tier": tier})

    def add_crm_activity(self, customer_id: str, activity_type: str, body: str) -> dict[str, Any]:
        return self.execute("crm_add_activity", {"customer_id": customer_id, "activity_type": activity_type, "body": body})

    def get_invoice(self, invoice_number: str) -> dict[str, Any]:
        return self.execute("billing_get_invoice", {"invoice_number": invoice_number})

    def calculate_refund(self, invoice_number: str, notice_date_iso: str = "2026-10-14T09:00:00Z") -> dict[str, Any]:
        return self.execute("billing_calculate_refund", {"invoice_number": invoice_number, "notice_date_iso": notice_date_iso})

    def issue_refund(self, invoice_number: str, amount_cents: int, reason: str) -> dict[str, Any]:
        return self.execute("billing_issue_refund", {"invoice_number": invoice_number, "amount_cents": amount_cents, "reason": reason})

    def list_tickets(self, status: str | None = None, customer_id: str | None = None) -> dict[str, Any]:
        return self.execute("tickets_list", {"status": status, "customer_id": customer_id})

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        return self.execute("tickets_get", {"ticket_id": ticket_id})

    def update_ticket(self, ticket_id: str, status: str | None = None, priority: str | None = None, comment: str | None = None) -> dict[str, Any]:
        return self.execute("tickets_update", {"ticket_id": ticket_id, "status": status, "priority": priority, "comment": comment})

    def search_kb(self, query: str) -> dict[str, Any]:
        return self.execute("kb_search", {"query": query})

    def get_kb_article(self, article_id: str) -> dict[str, Any]:
        return self.execute("kb_get_article", {"article_id": article_id})

    def run_command(self, command: str) -> dict[str, Any]:
        return self.execute("terminal_execute", {"command": command})

    def get_audit_events(self, limit: int = 50) -> dict[str, Any]:
        return self.execute("get_audit_events", {"limit": limit})

    def step_simulation(self, seconds: int = 60) -> dict[str, Any]:
        return self.execute("step_simulation", {"seconds": seconds})

    def submit_task(self, summary: str, affected_ids: list[str] | None = None) -> dict[str, Any]:
        return self.execute("submit_task", {"summary": summary, "affected_ids": affected_ids or []})

    def export_state(self) -> dict[str, Any]:
        return self.context.export_state()
