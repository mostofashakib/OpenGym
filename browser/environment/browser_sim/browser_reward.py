"""Multi-layered continuous reward and integrity evaluation for browser environment."""

from __future__ import annotations

from typing import Any
from browser_sim.browser_truth import (
    EXPECTED_CERT_CODE,
    EXPECTED_REJECTION_REASON,
    EXPECTED_RENEWAL_STATUS,
    EXPECTED_VENDOR_STATUS,
    MILESTONES,
    TARGET_COMPLIANCE_VENDOR,
    TARGET_FRAUD_PO,
    TARGET_RENEWAL_PO,
    TARGET_SHELL_VENDOR,
)


class IntegrityError(RuntimeError):
    kind = "integrity_error"

    def evidence(self) -> dict[str, Any]:
        return {}

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "message": str(self), **self.evidence()}


class MissingSectionsError(IntegrityError):
    kind = "missing_sections"

    def __init__(self, sections: list[str]) -> None:
        self.sections = sorted(sections)
        super().__init__(f"Workspace export is missing sections: {self.sections}")

    def evidence(self) -> dict[str, Any]:
        return {"sections": self.sections}


class DestroyedRegistryError(IntegrityError):
    kind = "destroyed_registry"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Critical portal entities were destroyed: {detail}")

    def evidence(self) -> dict[str, Any]:
        return {"detail": self.detail}


def evaluate_browser_episode(state: dict[str, Any]) -> dict[str, Any]:
    required_keys = ["orders", "vendors", "compliance_filings", "action_log"]
    missing = [k for k in required_keys if k not in state]
    if missing:
        raise MissingSectionsError(missing)

    orders = {o["id"]: o for o in state.get("orders", [])}
    vendors = {v["id"]: v for v in state.get("vendors", [])}
    filings = state.get("compliance_filings", [])
    action_log = state.get("action_log", [])
    submission = state.get("task_submission")

    if TARGET_FRAUD_PO not in orders or TARGET_RENEWAL_PO not in orders:
        raise DestroyedRegistryError("Target purchase orders vanished from database")
    if TARGET_SHELL_VENDOR not in vendors:
        raise DestroyedRegistryError("Vendor records vanished from database")

    # -------------------------------------------------------------
    # Layer 1: Progressive Navigation & Diagnostic Milestones (30%)
    # -------------------------------------------------------------
    milestones_achieved: dict[str, bool] = {}

    def _get_arg(a: dict[str, Any], key: str) -> str:
        args = a.get("arguments", {})
        if isinstance(args, str):
            try:
                import json
                args = json.loads(args)
            except Exception:
                args = {}
        if isinstance(args, dict):
            return str(args.get(key, ""))
        return ""

    visited_urls = [
        _get_arg(a, "url")
        for a in action_log
        if a["tool"] == "navigate"
    ]

    milestones_achieved["orders_page_visited"] = any("orders" in u for u in visited_urls)
    milestones_achieved["fraudulent_order_inspected"] = any(TARGET_FRAUD_PO in u for u in visited_urls) or any(
        TARGET_FRAUD_PO in str(a.get("arguments", "")) for a in action_log
    )

    # Fraud PO rejected
    fraud_po = orders.get(TARGET_FRAUD_PO, {})
    po_rejected = (
        fraud_po.get("status") in ("REJECTED", "CANCELLED")
        and fraud_po.get("rejection_reason") == EXPECTED_REJECTION_REASON
    )
    milestones_achieved["fraudulent_order_rejected"] = po_rejected

    # Renewal PO approved
    renewal_po = orders.get(TARGET_RENEWAL_PO, {})
    po_approved = renewal_po.get("status") == EXPECTED_RENEWAL_STATUS
    milestones_achieved["renewal_order_approved"] = po_approved

    # Vendor directory visited
    milestones_achieved["vendor_directory_visited"] = any("vendors" in u for u in visited_urls)

    # Shell vendor blacklisted
    shell_vend = vendors.get(TARGET_SHELL_VENDOR, {})
    vend_blacklisted = shell_vend.get("status") in (EXPECTED_VENDOR_STATUS, "SUSPENDED")
    milestones_achieved["shell_vendor_blacklisted"] = vend_blacklisted

    # Compliance page visited
    milestones_achieved["compliance_page_visited"] = any("compliance" in u for u in visited_urls)

    # SOC2 renewed
    has_valid_filing = any(
        f.get("vendor_id") == TARGET_COMPLIANCE_VENDOR
        and f.get("cert_reference") == EXPECTED_CERT_CODE
        for f in filings
    )
    datasync_vend = vendors.get(TARGET_COMPLIANCE_VENDOR, {})
    soc2_updated = has_valid_filing or datasync_vend.get("soc2_certified") == 1
    milestones_achieved["soc2_cert_renewed"] = soc2_updated

    # Task submitted
    report_submitted = submission is not None and bool(submission.get("summary"))
    milestones_achieved["audit_report_submitted"] = report_submitted

    milestone_score = sum(1.0 for k in MILESTONES if milestones_achieved.get(k, False)) / len(MILESTONES)

    # -------------------------------------------------------------
    # Layer 2: Final Portal State (40%)
    # -------------------------------------------------------------
    state_checks = [
        ("fraud_po_rejected_with_reason", po_rejected, 0.30),
        ("renewal_po_approved", po_approved, 0.20),
        ("shell_vendor_blacklisted", vend_blacklisted, 0.25),
        ("soc2_cert_filed", soc2_updated, 0.25),
    ]
    final_state_score = sum(w for _, passed, w in state_checks if passed)

    # -------------------------------------------------------------
    # Layer 3: Cleanliness & Operational Hygiene (30%)
    # -------------------------------------------------------------
    audit_findings: list[str] = []

    # Check that legitimate orders PO-1022 and PO-2045 remain APPROVED
    po1022 = orders.get("PO-1022", {})
    if po1022.get("status") != "APPROVED":
        audit_findings.append("legitimate_order_po1022_disrupted")

    po2045 = orders.get("PO-2045", {})
    if po2045.get("status") != "APPROVED":
        audit_findings.append("legitimate_order_po2045_disrupted")

    # Check that good tier-1 vendors were not blacklisted
    dell_vend = vendors.get("VEND-DELL", {})
    if dell_vend.get("status") != "ACTIVE":
        audit_findings.append("good_vendor_dell_disrupted")

    cloud_vend = vendors.get("VEND-CLOUDSCALE", {})
    if cloud_vend.get("status") != "ACTIVE":
        audit_findings.append("good_vendor_cloudscale_disrupted")

    cleanliness_score = max(0.0, 1.0 - (len(audit_findings) * 0.35))

    # -------------------------------------------------------------
    # Final Layer Aggregation
    # -------------------------------------------------------------
    weight_milestones = 0.30
    weight_final_state = 0.40
    weight_cleanliness = 0.30

    base_reward = (
        (milestone_score * weight_milestones)
        + (final_state_score * weight_final_state)
        + (cleanliness_score * weight_cleanliness)
    )

    success = 1.0 if (final_state_score >= 0.99 and report_submitted and not audit_findings) else 0.0

    return {
        "reward": round(base_reward, 6),
        "success": success,
        "valid": 1.0,
        "base_reward": round(base_reward, 6),
        "audit_pass": 1.0 if not audit_findings else 0.0,
        "audit_findings": len(audit_findings),
        "findings_detail": audit_findings,
        "layer_milestones": round(milestone_score, 6),
        "layer_weight_milestones": weight_milestones,
        "layer_final_state": round(final_state_score, 6),
        "layer_weight_final_state": weight_final_state,
        "layer_cleanliness": round(cleanliness_score, 6),
        "layer_weight_cleanliness": weight_cleanliness,
        "milestones_detail": milestones_achieved,
    }
