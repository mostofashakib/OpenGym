"""Canonical data models representing unified enterprise entities across 11 simulators."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Department:
    id: str
    name: str
    code: str
    lead_id: str


@dataclass
class Team:
    id: str
    name: str
    department_id: str
    lead_id: str


@dataclass
class Role:
    id: str
    title: str
    department: str
    approval_limit_usd: float
    permissions: List[str] = field(default_factory=list)


@dataclass
class Employee:
    id: str
    first_name: str
    last_name: str
    email: str
    role_id: str
    department_id: str
    team_id: str
    manager_id: Optional[str]
    title: str
    hire_date: str
    is_active: bool = True
    security_clearance: str = "standard"  # standard, elevated, executive


@dataclass
class Customer:
    id: str
    company_name: str
    tier: str  # enterprise, mid-market, smb
    account_owner_id: str  # Employee FK
    status: str  # active, churned, prospect
    arr_usd: float
    created_date: str


@dataclass
class Contact:
    id: str
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    title: str
    is_primary: bool = False


@dataclass
class Contract:
    id: str
    customer_id: str
    contract_number: str
    status: str  # active, expired, pending_renewal
    start_date: str
    end_date: str
    annual_value_usd: float
    sla_tier: str  # platinum, gold, silver, standard
    terms_text: str


@dataclass
class EmailMessage:
    id: str
    sender_email: str
    recipient_emails: List[str]
    cc_emails: List[str]
    subject: str
    body: str
    sent_iso: str
    thread_id: str
    is_read: bool = False
    folder: str = "inbox"  # inbox, sent, trash, drafts


@dataclass
class CalendarEvent:
    id: str
    title: str
    organizer_email: str
    attendee_emails: List[str]
    start_iso: str
    end_iso: str
    location: str = "Virtual Meeting"
    status: str = "confirmed"


@dataclass
class ChatChannel:
    id: str
    name: str
    channel_type: str  # public, private, direct
    member_ids: List[str]


@dataclass
class ChatMessage:
    id: str
    channel_id: str
    sender_id: str
    content: str
    timestamp_iso: str
    thread_id: Optional[str] = None


@dataclass
class CRMLead:
    id: str
    first_name: str
    last_name: str
    company: str
    email: str
    status: str  # new, contacted, qualified, lost
    owner_id: str


@dataclass
class CRMDeal:
    id: str
    customer_id: str
    title: str
    stage: str  # discovery, proposal, negotiation, closed_won, closed_lost
    amount_usd: float
    owner_id: str
    close_date: str


@dataclass
class SupportTicket:
    id: str
    customer_id: str
    contact_id: str
    title: str
    description: str
    priority: str  # low, medium, high, urgent
    status: str  # open, in_progress, pending_customer, pending_approval, resolved, closed
    assignee_id: Optional[str]
    created_iso: str
    resolved_iso: Optional[str] = None


@dataclass
class TicketComment:
    id: str
    ticket_id: str
    author_id: str
    is_internal: bool
    content: str
    created_iso: str


@dataclass
class FileFolder:
    id: str
    name: str
    parent_id: Optional[str] = None


@dataclass
class Document:
    id: str
    title: str
    folder_id: str
    author_id: str
    content: str
    version: int
    confidentiality_level: str  # public, internal, confidential, strictly_confidential
    updated_iso: str


@dataclass
class Invoice:
    id: str
    customer_id: str
    invoice_number: str
    amount_usd: float
    status: str  # draft, open, paid, void, uncollectible
    due_date: str
    issued_date: str


@dataclass
class Payment:
    id: str
    invoice_id: str
    customer_id: str
    amount_usd: float
    payment_method: str
    transaction_ref: str
    status: str  # succeeded, failed, refunded
    paid_iso: str


@dataclass
class RefundRecord:
    id: str
    invoice_id: str
    customer_id: str
    amount_usd: float
    reason: str
    requested_by_id: str
    approved_by_id: Optional[str]
    status: str  # pending_approval, approved, rejected, processed
    created_iso: str
    processed_iso: Optional[str] = None


@dataclass
class Project:
    id: str
    name: str
    lead_id: str
    status: str  # planning, active, paused, completed
    start_date: str
    target_date: str


@dataclass
class ProjectTask:
    id: str
    project_id: str
    title: str
    assignee_id: Optional[str]
    status: str  # backlog, todo, in_progress, in_review, done
    priority: str  # low, medium, high
    estimate_hours: float = 4.0


@dataclass
class KnowledgeArticle:
    id: str
    title: str
    category: str
    content: str
    author_id: str
    is_published: bool = True
    updated_iso: str = ""


@dataclass
class AuditLogEntry:
    id: int
    timestamp_iso: str
    actor_id: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    authorized: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyRule:
    id: str
    name: str
    category: str  # financial, data_protection, access_control, operational
    description: str
    rule_config: Dict[str, Any]
    severity: str = "critical"  # critical (fatal veto), warning (score penalty)
    is_active: bool = True
