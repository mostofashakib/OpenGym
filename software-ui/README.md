# Procedural SaaS Console (UI Environment)

> **OES-1 Specification Standard Environment**  
> **UI Port**: `3006`  
> **Service Name**: `software-ui`  
> **State Engine**: Authoritative SQLite Database (`software.db`)

---

## 1. Overview
`software-ui` provides a dynamic web console dynamically compiling declarative `AppSpec` schemas across 12+ specialized industry domains:

- Logistics & Fleet Routing
- Clinical Trial Management
- Aviation Maintenance & Safety
- Municipal Permitting
- Energy Grid Load Balancing
- Telecommunications Infrastructure
- Museum Archiving & Preservation
- Space Operations & Telemetry
- FinOps Cloud Infrastructure
- Venture Capital Deal Sourcing
- Maritime Cargo Dispatch
- Real Estate Asset Management

---

## 2. Architecture & Components
```
software-ui/
├── app/
│   ├── api/software/       # Schema, Entities, Transitions, Audit, Session endpoints
│   ├── globals.css         # Modern dark-theme styling
│   ├── layout.tsx          # Root layout with fake-time.js clock injection
│   └── page.tsx            # Interactive procedural SaaS console
├── environment/
│   └── software_sim/       # Dynamic procedural schema generator & SQLite DB
├── tools/
│   └── software_client.py  # Type-safe client communicating over socket/stdio
├── verifiers/
│   ├── layered.py          # Layered verifier (final_state, milestones, traj, negative veto)
│   ├── checks.py           # Verification assertions
│   └── auditor.py          # Anti-reward-hacking auditor
├── solution/
│   └── oracle.py           # Autonomous reference solver (1.000 score)
├── scripts/
│   └── software_bridge.py  # JSON-over-CLI bridge between Next.js & simulation
├── fake-time.js            # Deterministic browser/node virtual clock shim
├── run.sh                  # Development server bootstrapper (port 3006)
├── kill.sh                 # Graceful termination script
├── view.sh                 # Opens UI in default browser
├── audit.sh                # Verifies state hash & audit events
├── task.toml               # Harbor evaluation task specification
└── instruction.md          # Real-world agent operational prompt
```

---

## 3. Quick Start & Lifecycle Scripts
```bash
# Start Next.js development server on port 3006
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
