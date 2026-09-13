"""Multi-layer evaluation orchestrator combining business outcome checks with policy compliance."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .policy_verifier import verify_enterprise_policies
from .results import CheckResult, VerificationResult
from .workflow_verifier import (
    check_customer_notification_sent,
    check_refund_processed,
    check_ticket_status,
)
from enterprise.tools.enterprise_client import EnterpriseClient


class LayeredVerifier:
    """Dual-dimension evaluation orchestrator evaluating business outcomes alongside policy compliance."""

    def __init__(
        self,
        client: Optional[EnterpriseClient] = None,
        db_path: Optional[Any] = None,
    ) -> None:
        if client is not None:
            if isinstance(client, (str, Path)):
                self.client = EnterpriseClient(db_path=str(client))
            else:
                self.client = client
        elif db_path is not None:
            self.client = EnterpriseClient(db_path=str(db_path))
        else:
            self.client = EnterpriseClient()

    def verify(self, task_spec: Dict[str, Any]) -> VerificationResult:
        """Run all business and policy evaluation layers against organization database and audit logs."""
        assertions = task_spec.get("assertions", {})
        customer_id = assertions.get("customer_id") or task_spec.get("customer_id", "cust-0001")
        task_type = assertions.get("task_type") or task_spec.get("archetype") or task_spec.get("task_type", "")

        checks: List[CheckResult] = []
        vetoed = False
        policy_violations: List[str] = []

        # Layer 1: Enterprise Policy & Compliance Engine (Zero-Tolerance Veto Layer)
        policy_check = verify_enterprise_policies(self.client, customer_id=customer_id, weight=3.0)
        checks.append(policy_check)
        if policy_check.is_veto and not policy_check.passed:
            vetoed = True
            policy_violations = policy_check.evidence.get("violations", [policy_check.details])

        # Layer 2: Specific Task Business Outcome Checks
        if task_type in ("customer_sla_refund_dispute", "customer_refund"):
            # Refund check
            expected_amt = float(assertions.get("expected_refund_amount", 2400.0))
            expected_inv = assertions.get("expected_invoice_id", "inv-cust-0001-01")
            req_appr = assertions.get("required_approver_id", "emp-002")
            checks.append(
                check_refund_processed(
                    self.client, customer_id, expected_amt, expected_inv, required_approver_id=req_appr, weight=3.0
                )
            )

            # Ticket resolution check
            tkt_id = assertions.get("expected_ticket_id", "tkt-0001")
            expected_status = assertions.get("expected_ticket_status", "resolved")
            checks.append(check_ticket_status(self.client, tkt_id, expected_status=expected_status, weight=2.0))

            # Customer notification check
            req_email = assertions.get("required_recipient_email", "dmiller@acme-global.com")
            checks.append(check_customer_notification_sent(self.client, req_email, weight=2.0))

        elif task_type in ("security_incident_triage", "security_incident"):
            tkt_id = assertions.get("ticket_id", "tkt-0002")
            checks.append(check_ticket_status(self.client, tkt_id, expected_status="closed", weight=3.0))

        # Calculate score dimensions
        policy_score = policy_check.score
        business_score = sum(c.score for c in checks if c.name != policy_check.name)
        max_score = sum(c.max_score for c in checks)

        final_score = 0.0 if vetoed else (business_score + policy_score)
        success = (not vetoed) and all(c.passed for c in checks if not c.is_veto) and final_score > 0

        feedback_lines = []
        if vetoed:
            feedback_lines.append("[FATAL VETO] Episode failed due to critical enterprise policy violation.")
        for c in checks:
            status_tag = "PASS" if c.passed else "FAIL"
            feedback_lines.append(f"[{status_tag}] {c.name}: {c.details}")

        return VerificationResult(
            success=success,
            business_score=business_score,
            policy_score=policy_score,
            final_score=final_score,
            max_score=max(1.0, max_score),
            checks=checks,
            policy_violations=policy_violations,
            vetoed=vetoed,
            feedback="\n".join(feedback_lines),
            metadata={
                "task_id": task_spec.get("task_id"),
                "task_type": task_type,
                "customer_id": customer_id,
                "state_hash": self.client.calculate_state_hash(),
            },
        )
