"""JSON schema tool definitions for Workstation FastMCP and agents."""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "mail_list_threads",
        "description": "List email threads in a specified folder (inbox, sent, archive, trash).",
        "parameters": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "default": "inbox", "description": "Folder name"},
                "query": {"type": "string", "default": "", "description": "Search query"},
            },
        },
    },
    {
        "name": "mail_get_thread",
        "description": "Retrieve all messages in an email thread by thread ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "thread_id": {"type": "string", "description": "Thread ID (e.g. THREAD-ACME-CANCEL-01)"},
            },
            "required": ["thread_id"],
        },
    },
    {
        "name": "mail_send_message",
        "description": "Send a new email message or reply to a thread.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "array", "items": {"type": "string"}, "description": "Recipient email addresses"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Body text of the email"},
                "cc": {"type": "array", "items": {"type": "string"}, "description": "CC email addresses"},
                "thread_id": {"type": "string", "description": "Optional thread ID if replying"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "cal_list_events",
        "description": "List calendar events in a date range.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_iso": {"type": "string", "description": "Optional ISO start timestamp"},
                "end_iso": {"type": "string", "description": "Optional ISO end timestamp"},
            },
        },
    },
    {
        "name": "cal_create_event",
        "description": "Create a new meeting or debrief appointment on the workstation calendar.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_iso": {"type": "string", "description": "Start ISO 8601 timestamp"},
                "end_iso": {"type": "string", "description": "End ISO 8601 timestamp"},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "Attendee email addresses"},
                "description": {"type": "string", "default": "", "description": "Agenda or details"},
                "location": {"type": "string", "default": "", "description": "Meeting room or link"},
            },
            "required": ["title", "start_iso", "end_iso"],
        },
    },
    {
        "name": "drive_list_files",
        "description": "List files in the corporate Drive directory or search files by name/content.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "default": "/", "description": "Virtual directory (e.g. /contracts/, /finance/)"},
                "search": {"type": "string", "default": "", "description": "Search keyword"},
            },
        },
    },
    {
        "name": "drive_read_file",
        "description": "Read the text content and metadata of a file in Drive.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Virtual path (e.g. /contracts/Acme_Corp_MSA_Amendment_2026_Signed.pdf)"},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "drive_write_file",
        "description": "Write or update a file in the corporate Drive.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Virtual file path"},
                "content": {"type": "string", "description": "Text content of the file"},
                "mime_type": {"type": "string", "default": "text/plain", "description": "MIME type"},
                "customer_id": {"type": "string", "description": "Optional associated customer ID"},
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "crm_search_customers",
        "description": "Search customer accounts in the CRM by name, domain, or ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "crm_get_customer",
        "description": "Retrieve comprehensive CRM customer record, including contacts, deals, invoices, and activity logs.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID (e.g. CUST-1042)"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "crm_update_customer",
        "description": "Update customer account status (e.g. active, churned, paused), tier, or phone.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "status": {"type": "string", "description": "New account status (e.g. churned, active)"},
                "account_tier": {"type": "string", "description": "Account tier"},
                "phone": {"type": "string", "description": "Phone number"},
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "crm_add_activity",
        "description": "Log an activity note, call record, or email log on a CRM customer account.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID"},
                "activity_type": {"type": "string", "description": "Type (note, call, email, status_change)"},
                "body": {"type": "string", "description": "Activity description and details"},
            },
            "required": ["customer_id", "activity_type", "body"],
        },
    },
    {
        "name": "billing_get_invoice",
        "description": "Get invoice details, payment status, and any issued refunds.",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string", "description": "Invoice number (e.g. INV-3817)"},
            },
            "required": ["invoice_number"],
        },
    },
    {
        "name": "billing_calculate_refund",
        "description": "Calculate allowed pro-rated refund and administrative fee based on contract start date and notice date.",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string", "description": "Invoice number"},
                "notice_date_iso": {"type": "string", "default": "2026-10-14T09:00:00Z", "description": "Notice date"},
            },
            "required": ["invoice_number"],
        },
    },
    {
        "name": "billing_issue_refund",
        "description": "Process and issue a pro-rated or full refund for a paid invoice in the billing system.",
        "parameters": {
            "type": "object",
            "properties": {
                "invoice_number": {"type": "string", "description": "Invoice number"},
                "amount_cents": {"type": "integer", "description": "Refund amount in integer cents"},
                "reason": {"type": "string", "description": "Business reason for the refund"},
            },
            "required": ["invoice_number", "amount_cents", "reason"],
        },
    },
    {
        "name": "tickets_list",
        "description": "List customer support tickets filtered by status or customer ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Status filter (open, in_progress, resolved, closed)"},
                "customer_id": {"type": "string", "description": "Customer ID filter"},
            },
        },
    },
    {
        "name": "tickets_get",
        "description": "Get support ticket details and conversation comments.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "Ticket ID (e.g. TICK-2042)"},
            },
            "required": ["ticket_id"],
        },
    },
    {
        "name": "tickets_update",
        "description": "Update ticket status (e.g. resolved, in_progress) and optionally post a resolution comment.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "Ticket ID"},
                "status": {"type": "string", "description": "New status (open, in_progress, resolved, closed)"},
                "priority": {"type": "string", "description": "New priority"},
                "comment": {"type": "string", "description": "Optional comment or resolution note"},
            },
            "required": ["ticket_id"],
        },
    },
    {
        "name": "kb_search",
        "description": "Search the internal corporate knowledge base and standard operating procedures (SOPs).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords (e.g. cancellation, refund, privacy)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "kb_get_article",
        "description": "Read the full text of a knowledge base article or policy document.",
        "parameters": {
            "type": "object",
            "properties": {
                "article_id": {"type": "string", "description": "Article ID (e.g. KB-OPS-042)"},
            },
            "required": ["article_id"],
        },
    },
    {
        "name": "terminal_execute",
        "description": "Execute a simulated workstation command (whoami, date, hostname, uptime, ls).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "get_audit_events",
        "description": "Retrieve recent action logs and event trail from the workstation append-only audit log.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50, "description": "Maximum number of audit events to return"},
            },
        },
    },
    {
        "name": "step_simulation",
        "description": "Advance workstation virtual clock deterministically by specified seconds.",
        "parameters": {
            "type": "object",
            "properties": {
                "seconds": {"type": "integer", "default": 60, "description": "Number of seconds to advance virtual time"},
            },
        },
    },
    {
        "name": "submit_task",
        "description": "Submit final completion report for the workstation operational task.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Summary of actions performed and resolution details"},
                "affected_ids": {"type": "array", "items": {"type": "string"}, "description": "List of affected entity IDs"},
            },
            "required": ["summary"],
        },
    },
]
