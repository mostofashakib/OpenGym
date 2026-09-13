"""Canonical dataclasses representing Workstation entities across all 8 applications."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    email: str
    role: str
    department: str
    manager_id: str | None = None
    phone: str = ""
    permissions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Customer:
    id: str
    name: str
    domain: str
    account_tier: str = "standard"
    status: str = "active"
    phone: str = ""
    primary_contact_id: str | None = None
    msa_date: str = ""
    created_ts: str = ""


@dataclass(frozen=True)
class CRMContact:
    id: str
    customer_id: str
    name: str
    email: str
    phone: str = ""
    title: str = ""
    notes: str = ""
    is_primary: bool = False


@dataclass(frozen=True)
class CRMDeal:
    id: str
    customer_id: str
    title: str
    value_cents: int = 0
    stage: str = "open"
    owner_id: str | None = None
    close_date_iso: str | None = None


@dataclass(frozen=True)
class CRMActivityLog:
    id: int
    customer_id: str
    timestamp_iso: str
    author: str
    activity_type: str
    body: str


@dataclass(frozen=True)
class EmailThread:
    id: str
    subject: str
    customer_id: str | None
    last_activity_iso: str
    snippet: str
    message_count: int = 1


@dataclass(frozen=True)
class EmailMessage:
    id: str
    thread_id: str
    sender: str
    recipients: list[str]
    cc: list[str]
    subject: str
    body: str
    timestamp_iso: str
    folder: str = "inbox"
    is_read: bool = True


@dataclass(frozen=True)
class CalendarEvent:
    id: str
    title: str
    start_iso: str
    end_iso: str
    attendees: list[str]
    description: str = ""
    location: str = ""
    organizer: str = ""


@dataclass(frozen=True)
class DriveFile:
    id: str
    path: str
    name: str
    mime_type: str
    size_bytes: int
    content_text: str
    updated_at_iso: str
    version: int = 1
    customer_id: str | None = None


@dataclass(frozen=True)
class Ticket:
    id: str
    customer_id: str
    title: str
    description: str
    priority: str
    status: str
    assigned_to: str | None
    created_at_iso: str
    updated_at_iso: str


@dataclass(frozen=True)
class TicketComment:
    id: int
    ticket_id: str
    author: str
    content: str
    created_at_iso: str
    is_internal: bool = False


@dataclass(frozen=True)
class Invoice:
    id: str
    customer_id: str
    invoice_number: str
    amount_cents: int
    currency: str
    status: str
    period_start: str
    period_end: str
    paid_at_iso: str | None


@dataclass(frozen=True)
class Refund:
    id: str
    invoice_id: str
    customer_id: str
    amount_cents: int
    currency: str
    reason: str
    issued_at_iso: str
    issued_by: str


@dataclass(frozen=True)
class KBArticle:
    id: str
    category: str
    title: str
    slug: str
    body: str
    created_at_iso: str


@dataclass(frozen=True)
class ActionLog:
    id: int
    timestamp_iso: str
    actor: str
    application: str
    action: str
    target_type: str = ""
    target_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
