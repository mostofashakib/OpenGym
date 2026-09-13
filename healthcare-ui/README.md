# Aegis Health Clinical EHR (UI Environment)

> **OES-1 Specification Standard Environment**  
> **UI Port**: `3007`  
> **Service Name**: `healthcare-ui`  
> **State Engine**: Authoritative SQLite Database (`healthcare.db`)

---

## 1. Overview
`healthcare-ui` simulates **Aegis Health**, a production-grade Electronic Health Record (EHR) system adhering to FHIR R4 clinical data models and zero-tolerance patient safety invariants:

- **2-Factor Patient Identity Verification**: Mandates MRN/ID and birth date matching prior to clinical interventions.
- **Longitudinal Clinical Charts**: Patient demographics, conditions, encounters, diagnostic labs, vitals, allergies, and active medications.
- **Safety Invariant Enforcement**:
  - Allergy contraindications (e.g. penicillin cross-reactivity).
  - Drug-drug interactions (e.g. Warfarin + NSAIDs).
  - Renal dosing ceilings (e.g. Metformin with severe renal impairment).
- **Prior Authorization & Insurance Workflow**: Structured clinical justifications and attachment tracking.
- **Emergency Triage Escalation**: Red-flag symptom detection and immediate transfer to human clinician.
- **HIPAA Minimum-Necessary Access Audit**: Append-only access logging detecting and penalizing unmotivated record snooping.

---

## 2. Architecture & Components
```
healthcare-ui/
├── app/
│   ├── api/healthcare/     # Patients, Orders, Portal, Audit, Simulation endpoints
│   ├── globals.css         # Modern dark-theme styling
│   ├── layout.tsx          # Root layout with fake-time.js clock injection
│   └── page.tsx            # Interactive Aegis Health Clinical EHR console
├── environment/
│   └── healthcare_sim/     # FHIR clinical models, safety engine & SQLite DB
├── tools/
│   └── healthcare_client.py # Type-safe client communicating over socket/stdio
├── verifiers/
│   ├── layered.py          # Layered verifier (final_state, milestones, traj, negative veto)
│   ├── checks.py           # Clinical safety invariant checks
│   └── auditor.py          # Anti-reward-hacking auditor
├── solution/
│   └── oracle.py           # Autonomous reference solver (1.000 score)
├── scripts/
│   └── healthcare_bridge.py # JSON-over-CLI bridge between Next.js & simulation
├── fake-time.js            # Deterministic browser/node virtual clock shim
├── run.sh                  # Development server bootstrapper (port 3007)
├── kill.sh                 # Graceful termination script
├── view.sh                 # Opens UI in default browser
├── audit.sh                # Verifies state hash & HIPAA audit events
├── task.toml               # Harbor evaluation task specification
└── instruction.md          # Real-world agent operational prompt
```

---

## 3. Quick Start & Lifecycle Scripts
```bash
# Start Next.js development server on port 3007
./run.sh

# Open web interface in default browser
./view.sh

# Audit system state hash and HIPAA access log
./audit.sh

# Run automated test suite
./tests/test.sh

# Stop server and clean up ports
./kill.sh
```
