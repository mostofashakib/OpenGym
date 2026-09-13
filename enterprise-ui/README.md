# Apex Enterprise Cloud (UI Environment)

> **OES-1 Specification Standard Environment**  
> **UI Port**: `3005`  
> **Service Name**: `enterprise-ui`  
> **State Engine**: Authoritative SQLite Database (`company.db` / `enterprise.db`)

---

## 1. Overview
`enterprise-ui` simulates **Apex Enterprise Cloud**, a mission-critical multi-system enterprise operations platform connecting 11 interconnected systems:

- **Customer 360**: Unified accounts, contacts, active contracts, recent invoices, and CRM deal pipelines.
- **Support Operations Desk**: Tiered incident management with real-time Data Loss Prevention (DLP) outbound scanning.
- **Approvals & Governance**: Dual-control approval workflows enforcing segregation of duties and role spending caps.
- **Billing & SLA Concessions**: Refund processing validating financial authority matrix and contractual SLA concession caps.
- **Org Directory**: Complete hierarchy across 5 departments, teams, employee roles, and manager structures.
- **Audit & Compliance**: Immutable cryptographically verifiable event stream with SHA-256 database state hashing.

---

## 2. Architecture & Components
```
enterprise-ui/
├── app/
│   ├── api/enterprise/     # Org, Customers, Support, Billing, Approvals, Comms, Audit endpoints
│   ├── globals.css         # Modern dark-theme styling
│   ├── layout.tsx          # Root layout with fake-time.js clock injection
│   └── page.tsx            # Interactive Apex Enterprise Cloud operations console
├── environment/
│   └── enterprise_sim/     # 11-system simulation engine, policy engine & SQLite DB
├── tools/
│   └── enterprise_client.py # Type-safe client communicating over socket/stdio
├── verifiers/
│   ├── layered.py          # Layered verifier (final_state, milestones, traj, negative veto)
│   ├── checks.py           # Enterprise policy & SLA invariant checks
│   └── auditor.py          # Anti-reward-hacking auditor
├── solution/
│   └── oracle.py           # Autonomous reference solver (1.000 score)
├── scripts/
│   └── enterprise_bridge.py # JSON-over-CLI bridge between Next.js & simulation
├── fake-time.js            # Deterministic browser/node virtual clock shim
├── run.sh                  # Development server bootstrapper (port 3005)
├── kill.sh                 # Graceful termination script
├── view.sh                 # Opens UI in default browser
├── audit.sh                # Verifies state hash & enterprise audit events
├── task.toml               # Harbor evaluation task specification
└── instruction.md          # Real-world agent operational prompt
```

---

## 3. Quick Start & Lifecycle Scripts
```bash
# Start Next.js development server on port 3005
./run.sh

# Open web interface in default browser
./view.sh

# Audit system state hash and events
./audit.sh

# Run automated test suite
./tests/test.sh

# Stop server and clean up ports
./kill.sh
```
