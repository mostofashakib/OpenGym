# OpenGym — Long-Horizon Computer Use Workstation

A comprehensive, deterministic, multi-application employee workstation simulation for evaluating and benchmarking AI agents on complex, long-horizon computer-use tasks in [OpenGym](https://github.com/mostofashakib/OpenGym).

---

## Overview

The Workstation environment simulates a complete enterprise employee computer. Rather than isolating single tools, it unifies an entire organization across 8 interconnected application surfaces:

| Application | Role & Simulated Capabilities |
|---|---|
| **Email Client (`mail_*`)** | Inbox, sent, threads, attachments, multi-recipient messages, CC/BCC |
| **Calendar (`cal_*`)** | Schedule meetings, invite attendees, inspect recurring events and rooms |
| **Drive / File Manager (`drive_*`)** | Hierarchical files (`.pdf`, `.xlsx`, `.docx`, `.txt`, `.csv`, `.json`), contracts, policies |
| **CRM System (`crm_*`)** | Customer accounts, deals, pipeline stages, contacts, activity audit notes |
| **Billing & Invoices (`billing_*`)** | Invoices, payment ledgers, pro-rated refund calculations, refund issuance |
| **Support Ticketing (`tickets_*`)** | Customer tickets, priorities, resolution statuses, internal comments |
| **Knowledge Base (`kb_*`)** | Corporate SOPs, calculation formulas, compliance & security policies |
| **Terminal / Shell (`terminal_*`)** | Simulated command execution (`whoami`, `date`, `hostname`, `ls`, etc.) |

All applications share a single underlying canonical state: an action taken in one tool immediately reflects across all other tools.

---

## Key Architecture Principles

1. **Persistent Canonical State**:
   A hidden SQLite database holds all authoritative records (employees, customers, deals, emails, calendar events, files, invoices, refunds, tickets, and action audit logs). The agent interacts strictly via tools and UI observations.
2. **Deterministic Reset & State Hashing**:
   Resetting with a given `(seed, task_id)` regenerates the exact same virtual world. A canonical SHA-256 state hash guarantees byte-for-byte reproducibility across runs.
3. **Realistic Noise & Ambiguity**:
   The dataset features intentional real-world messy data:
   - Homoglyphic & similar names (e.g. `Sarah Jenkins` vs `Sara Jenkens`).
   - Superseded contracts (e.g. `Acme_Corp_MSA_2023_Archived.pdf` with no-refund terms superseded by `Acme_Corp_MSA_Amendment_2026_Signed.pdf`).
   - Outdated contact information and abbreviation aliases.
4. **Controlled Disturbances**:
   Optionally injects transient network latency (HTTP 503), session expirations, and conflicting edits via `WORKSTATION_DISTURBANCE_RATE`.
5. **Multi-Predicate Verifier & Privacy Auditor**:
   Evaluates 7 distinct state and procedural predicates, plus auditing for:
   - **Privacy violations**: penalizes inspecting customer accounts outside the task scope.
   - **Causal ordering**: penalizes sending confirmation messages before financial transactions settle.

---

## Quick Start & Verification

```bash
# Run the complete test suite (13 tests)
pytest tests -v

# Run Harbor test script (pytest + oracle self-verification)
./tests/test.sh

# Run the deterministic reference oracle (scores 1.0)
python3 -m solution.oracle
```

---

## Harbor Benchmark Execution

```bash
# Run with Harbor and oracle agent
harbor run -p ./workstation -a oracle

# Run with local model (e.g. Ollama)
./workstation/run.sh
```
