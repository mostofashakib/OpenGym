# OpenGym: Browser Procurement Portal UI Environment (`browser-ui`)

Interactive Enterprise Procurement & Compliance Portal for AI agent evaluation and training under the [Harbor](https://github.com/avahr/harbor) framework.

## Overview

`browser-ui` provides a rich web application (`https://procure.corp`) modeling an enterprise procurement, purchase order approval, and third-party risk management portal.

### Key Capabilities & Interface
- **Executive Procurement Dashboard**: Summary KPI cards showing pending order volumes, critical vendor risks, and expired SOC-2 certifications.
- **Purchase Orders Registry**: Interactive ledger to examine requisitions, inspect items and spend amounts, approve legitimate software renewals, and reject fraudulent requisitions with policy justification.
- **Vendor Directory & Risk Registry**: Detailed third-party risk profiles, active contract statuses, and immediate 1-click vendor blacklisting.
- **SOC-2 Type II Compliance Center**: Interactive filing interface to verify and renew overdue vendor compliance certifications (`SOC2-2026-DS-882`).
- **Comprehensive Audit Sign-Off**: Structured audit filing form with executive summary and multi-entity confirmation checklist.
- **Dual Interaction Modes**: Direct FastMCP stdio server for LLM agents, and REST API routes under `/api/browser/...` for web / browser agents.

---

## Scenario: Q3 Procurement & Compliance Audit

As the Lead Compliance Auditor on `https://procure.corp`:
1. **Quarantine Fraudulent Requisition**: Inspect `PO-9821` (a $480,000 GPU cluster requested by an unverified user) and reject it with audit rationale.
2. **Approve Verified Renewal**: Review and approve `PO-3410` ($18,500 enterprise Kubernetes license renewal from tier-1 partner `CloudScale Systems Inc.`).
3. **Blacklist Shell Entity**: Locate unverified offshore supplier `GhostWire Hardware LLC` (`VEND-GHOSTWIRE`) and revoke authorization by setting status to `BLACKLISTED`.
4. **Recertify Cloud Backup Partner**: File the renewed SOC-2 Type II audit reference `SOC2-2026-DS-882` for `DataSync Corp` (`VEND-DATASYNC`), whose prior certification expired 30 days ago.
5. **File Formal Audit Report**: Submit the final audit sign-off covering all four audited entities.

---

## Running Locally

### Development Server (Next.js)
```bash
cd browser-ui
npm install
npm run dev # Starts web UI on http://localhost:3001
```

### Self-Tests & Verifier
```bash
./tests/test.sh
```

### Reference Solution Oracle
```bash
./solution/solve.sh
```

### Harbor Run
```bash
./run.sh
```
