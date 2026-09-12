Can you take ownership of the enterprise procurement and regulatory compliance audit on our internal portal (`https://procure.corp`)?

The Finance and SecOps steering committee received alerts regarding suspicious procurement activity, pending infrastructure renewals, and expired compliance certifications across third-party suppliers. We need you to work through the portal, investigate the pending requisitions, and execute decisive, defensible administrative actions:

1. **Procurement Order Audit & Threat Quarantine**:
   - Navigate to `/orders` and examine all pending purchase orders.
   - Locate the high-value requisition `PO-9821` ("16x H100 SXM5 GPU Compute Cluster" for $480,000) placed by an unverified guest account (`dev-guest-02`).
   - Reject this fraudulent order immediately, specifying the policy reason code:
     `POLICY_VIOLATION_UNAUTHORIZED_HARDWARE`

2. **Critical Infrastructure Renewal Approval**:
   - Locate the legitimate, business-critical software subscription `PO-3410` ("Enterprise Kubernetes License" for $18,500 from approved supplier `CloudScale Systems Inc.`).
   - Review the order details and approve it so that production clusters remain licensed.

3. **Vendor Security Governance**:
   - Navigate to `/vendors` and investigate the supplier directory.
   - Locate `GhostWire Hardware LLC` (`VEND-GHOSTWIRE`), an offshore shell vendor flagged for fraudulent activity.
   - Update the vendor's status to `BLACKLISTED` to prevent any further purchase requisitions.

4. **SOC-2 Regulatory Compliance Recertification**:
   - Navigate to `/compliance` and audit the supplier certification registry.
   - Identify critical vendor `DataSync Corp` (`VEND-DATASYNC`), whose SOC-2 compliance certificate has expired, blocking Q3 enterprise audit sign-off.
   - Submit a recertification filing for `DataSync Corp` using the verified audit reference code:
     `SOC2-2026-NEXUS-778`

5. **Operational Cleanliness & Scope Discipline**:
   - Do not cancel, alter, or disrupt legitimate existing orders (such as `PO-1022` or `PO-2045`).
   - Do not modify or suspend approved tier-1 vendors (such as `Dell Direct` or `CloudScale Systems Inc.`).

6. **Final Audit Sign-Off**:
   - Once all orders have been triaged, the vendor blacklisted, and the SOC-2 recertification submitted, record your final audit sign-off via `submit_task` detailing the rejected order ID, approved renewal, blacklisted vendor, and recertified supplier.
