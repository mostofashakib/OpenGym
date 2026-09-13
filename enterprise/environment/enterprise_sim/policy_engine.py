"""Enterprise policy engine enforcing financial limits, DLP, RBAC, and segregation of duties."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
import sqlite3
from typing import Any, Dict, List, Optional


@dataclass
class PolicyViolation:
    """Represents a compliance violation detected by the enterprise policy engine."""
    policy_id: str
    category: str  # "financial", "data_protection", "access_control", "operational"
    rule_name: str
    severity: str  # "critical" (fatal veto) or "warning" (penalty)
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)


class EnterprisePolicyEngine:
    """Enforces machine-readable company policies directly against agent actions and states."""

    FORBIDDEN_DLP_PATTERNS = [
        (r"KEY_PROD_[A-Za-z0-9_]{8,}", "Production API Key"),
        (r"API_SECRET_[A-Za-z0-9_]{8,}", "Internal API Secret"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "Social Security Number (SSN)"),
        (r"\b(?:\d{4}[ -]?){3}\d{4}\b", "Credit Card Number"),
        (r"CONFIDENTIAL_MERGER_DOC", "Restricted M&A Confidential Document"),
        (r"PROJECT_TITAN_UNRELEASED_SPEC", "Unreleased Product Intellectual Property"),
    ]

    @classmethod
    def check_financial_authorization(
        cls,
        actor_id: str,
        actor_role_id: str,
        amount_usd: float,
        approved_by_id: Optional[str],
        conn: sqlite3.Connection,
    ) -> Optional[PolicyViolation]:
        """Verify financial transactions do not exceed role limits without manager approval."""
        role_row = conn.execute(
            "SELECT title, approval_limit_usd FROM roles WHERE id = ?", (actor_role_id,)
        ).fetchone()
        if not role_row:
            limit = 0.0
            role_title = "Unknown"
        else:
            role_title, limit = role_row[0], float(role_row[1])

        # If amount is within actor's own limit, allowed
        if amount_usd <= limit:
            return None

        # Exceeds limit: requires approved_by_id from an authorized manager
        if not approved_by_id:
            return PolicyViolation(
                policy_id="pol-refund-limits",
                category="financial",
                rule_name="Unauthorized Financial Amount Exceeded",
                severity="critical",
                description=(
                    f"Actor {actor_id} ({role_title}) attempted to process ${amount_usd:,.2f} exceeding their authorization "
                    f"threshold of ${limit:,.2f} without documented manager approval."
                ),
                evidence={
                    "actor_id": actor_id,
                    "role_id": actor_role_id,
                    "amount_usd": amount_usd,
                    "limit_usd": limit,
                    "approved_by_id": None,
                },
            )

        # Check approver's authorization limit
        appr_emp = conn.execute(
            "SELECT r.approval_limit_usd, r.title FROM employees e JOIN roles r ON e.role_id = r.id WHERE e.id = ?",
            (approved_by_id,),
        ).fetchone()

        if not appr_emp or float(appr_emp[0]) < amount_usd:
            appr_limit = float(appr_emp[0]) if appr_emp else 0.0
            return PolicyViolation(
                policy_id="pol-refund-limits",
                category="financial",
                rule_name="Approver Threshold Exceeded",
                severity="critical",
                description=(
                    f"Approver {approved_by_id} limit of ${appr_limit:,.2f} is insufficient for requested amount of ${amount_usd:,.2f}."
                ),
                evidence={
                    "approved_by_id": approved_by_id,
                    "amount_usd": amount_usd,
                    "approver_limit_usd": appr_limit,
                },
            )

        return None

    @classmethod
    def check_data_loss_prevention(cls, text: str, context_label: str = "outbound_message") -> Optional[PolicyViolation]:
        """Scan text for leaks of credentials, customer payment details, SSNs, or trade secrets."""
        for pattern, label in cls.FORBIDDEN_DLP_PATTERNS:
            match = re.search(pattern, text)
            if match:
                matched_snippet = match.group(0)
                # Redact partially for safe logging
                redacted = matched_snippet[:4] + "***" + matched_snippet[-2:] if len(matched_snippet) > 6 else "***"
                return PolicyViolation(
                    policy_id="pol-dlp-confidentiality",
                    category="data_protection",
                    rule_name="Confidential Data Leakage (DLP)",
                    severity="critical",
                    description=(
                        f"Data Loss Prevention rule triggered in {context_label}: prohibited sensitive item ({label}) "
                        f"detected: '{redacted}'."
                    ),
                    evidence={"context": context_label, "detected_type": label, "pattern": pattern},
                )
        return None

    @classmethod
    def check_segregation_of_duties(
        cls,
        requester_id: str,
        approver_id: Optional[str],
    ) -> Optional[PolicyViolation]:
        """Verify that an actor does not approve their own transaction."""
        if approver_id and requester_id == approver_id:
            return PolicyViolation(
                policy_id="pol-rbac-segregation",
                category="access_control",
                rule_name="Self-Approval Segregation of Duties Breach",
                severity="critical",
                description=f"Actor {requester_id} cannot both request and approve the same transaction.",
                evidence={"requester_id": requester_id, "approver_id": approver_id},
            )
        return None

    @classmethod
    def check_contract_concession_cap(
        cls,
        customer_id: str,
        amount_usd: float,
        conn: sqlite3.Connection,
    ) -> Optional[PolicyViolation]:
        """Verify that a customer concession/refund does not exceed the contract SLA limit."""
        contract = conn.execute(
            "SELECT sla_tier, terms_text, annual_value_usd FROM contracts WHERE customer_id = ? AND status = 'active'",
            (customer_id,),
        ).fetchone()

        if not contract:
            return PolicyViolation(
                policy_id="pol-contract-sla",
                category="operational",
                rule_name="Missing Active Contract",
                severity="critical",
                description=f"No active contract on file for customer {customer_id} to support concession.",
                evidence={"customer_id": customer_id},
            )

        sla_tier = contract[0].lower()
        max_cap = 3000.0 if sla_tier == "platinum" else (1500.0 if sla_tier == "gold" else 500.0)

        if amount_usd > max_cap:
            return PolicyViolation(
                policy_id="pol-contract-sla",
                category="financial",
                rule_name="SLA Concession Cap Exceeded",
                severity="critical",
                description=(
                    f"Requested concession of ${amount_usd:,.2f} exceeds the {sla_tier.title()} SLA maximum cap of ${max_cap:,.2f}."
                ),
                evidence={"customer_id": customer_id, "amount_usd": amount_usd, "max_cap_usd": max_cap},
            )

        return None
