# OmniDesk Employee Workstation OS (UI Environment)

> **OES-1 Specification Standard Environment**  
> **UI Port**: `3008`  
> **Service Name**: `workstation-ui`  
> **State Engine**: Authoritative SQLite Database (`workstation.db`)

---

## 1. Overview
`workstation-ui` provides a pixel-perfect, highly responsive graphical desktop operating system simulating a modern employee workstation with 12 synchronized applications:

1. **Customer Relationship Management (CRM)**: Manage customer accounts, revenue, and contacts.
2. **Support Ticket Desk**: Triage and resolve technical incidents across SLA priorities.
3. **Email Suite**: Inbox, sent folders, thread inspection, and DLP-guarded composition.
4. **Team Chat / Slack**: Multi-channel team communication and collaborative incident triage.
5. **Interactive Terminal / Shell**: Command execution, diagnostic pipelines, and logs.
6. **File Manager**: Directory navigation, permissions, and file content preview.
7. **Web Browser**: Simulated intranet browser with URL bar, bookmarks, and page rendering.
8. **Calendar**: Schedule team meetings, sprint planning, and emergency syncs.
9. **Notes**: Scratchpad for operational documentation and investigation logs.
10. **System Settings**: Role configuration, display settings, and notification controls.
11. **Clock & Time Synchronizer**: Virtual time advancement (`fake-time.js`) preserving determinism.
12. **Audit & Compliance Monitor**: Real-time event tracking and cryptographic SHA-256 state hashing.

---

## 2. Architecture & Directory Structure
```
workstation-ui/
├── app/
│   ├── api/workstation/    # 12 Next.js REST API endpoints
│   ├── globals.css         # Modern dark-theme styling
│   ├── layout.tsx          # Root layout with fake-time.js clock injection
│   └── page.tsx            # Multi-window OmniDesk OS interactive desktop
├── environment/
│   └── workstation_sim/    # Authoritative world simulation engine & SQLite DB
├── tools/
│   └── workstation_client.py # Type-safe client communicating over socket/stdio
├── verifiers/
│   ├── layered.py          # Layered verifier (final_state, milestones, traj, negative veto)
│   ├── checks.py           # Verification assertions
│   └── auditor.py          # Anti-reward-hacking auditor
├── solution/
│   └── oracle.py           # Autonomous reference solver (1.000 score)
├── scripts/
│   └── workstation_bridge.py # JSON-over-CLI bridge between Next.js & simulation
├── fake-time.js            # Deterministic browser/node virtual clock shim
├── run.sh                  # Development server bootstrapper (port 3008)
├── kill.sh                 # Graceful termination script
├── view.sh                 # Opens UI in default browser
├── audit.sh                # Verifies state hash & audit events
├── task.toml               # Harbor evaluation task specification
└── instruction.md          # Real-world agent operational prompt
```

---

## 3. Quick Start & Lifecycle Scripts
```bash
# Start Next.js development server on port 3008
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
