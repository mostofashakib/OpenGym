"""Ground truth definitions and constants for browser procurement audit verification."""

from __future__ import annotations

TARGET_FRAUD_PO = "PO-9821"
EXPECTED_REJECTION_REASON = "POLICY_VIOLATION_UNAUTHORIZED_HARDWARE"

TARGET_RENEWAL_PO = "PO-3410"
EXPECTED_RENEWAL_STATUS = "APPROVED"

TARGET_SHELL_VENDOR = "VEND-GHOSTWIRE"
EXPECTED_VENDOR_STATUS = "BLACKLISTED"

TARGET_COMPLIANCE_VENDOR = "VEND-DATASYNC"
EXPECTED_CERT_CODE = "SOC2-2026-NEXUS-778"

# Milestones for progressive diagnostic tracking
MILESTONES = (
    "orders_page_visited",
    "fraudulent_order_inspected",
    "fraudulent_order_rejected",
    "renewal_order_approved",
    "vendor_directory_visited",
    "shell_vendor_blacklisted",
    "compliance_page_visited",
    "soc2_cert_renewed",
    "audit_report_submitted",
)
