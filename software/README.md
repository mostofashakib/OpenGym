# Generative Software Environment (`software/`)

A procedural software application generator and benchmark environment for testing agent generalization across diverse business domains, custom schemas, non-standard UI layouts, lifecycle state machines, and relational workflows.

---

## 1. Overview & Motivation

Conventional benchmarks test AI agents inside static, familiar software products (such as Salesforce, Gmail, or GitHub). Agents can easily memorize fixed schemas, navigation menus, and DOM hierarchies without actually mastering transferable concepts such as:
- Searching and filtering entity records
- Navigating unfamiliar terminology and information architectures
- Discovering and respecting finite-state machine lifecycles
- Resolving multi-step prerequisite dependencies
- Enforcing role-based access control (RBAC)
- Handling edge cases (missing data, malformed records, blocked transitions)

`software/` procedurally generates entire software applications from declarative specifications (`AppSpec`), yielding thousands of distinct business application configurations.

---

## 2. Declarative Architecture

Every generated application is governed by a declarative specification (`AppSpec`):
- **Entities & Fields**: Strongly typed (`string`, `integer`, `float`, `boolean`, `enum`, `foreign_key`, `text`, `timestamp`).
- **Relational Integrity**: Foreign key constraints with one-to-many and many-to-one topologies.
- **Workflow State Machines**: Directed state graphs with permitted actions, source/target states, and required roles.
- **RBAC Roles & Permissions**: Configurable access layers (`admin`, `manager`, `operator`, `auditor`).
- **UI Layout & Information Architecture**: Four layout archetypes (`sidebar_table`, `nested_tree_cards`, `split_workspace`, `tabbed_board`) with dynamic terminology mapping.

---

## 3. Supported Domain Templates (20 Diverse Domains)

The environment includes 20 procedural domain templates:

| Domain Key | Application Title | Primary Entity | Secondary Entity | Sample Actions |
|---|---|---|---|---|
| `logistics` | Freight Operations Suite | `Shipment` | `Exception` | `dispatch`, `flag_delay`, `confirm_delivery` |
| `higher_ed` | Campus Registrar Suite | `OverrideRequest` | `Course` | `submit_to_faculty`, `escalate_to_dean`, `approve` |
| `equipment` | Fleet Maintenance Hub | `WorkOrder` | `Asset` | `assign_tech`, `hold_for_parts`, `complete` |
| `research` | Lab Specimen Tracking | `Assay` | `Sample` | `queue_run`, `flag_contamination`, `publish_results` |
| `real_estate` | Commercial Property Ops | `LeaseAgreement` | `Property` | `draft`, `underwrite`, `countersign`, `terminate` |
| `clinical_trials` | Patient Cohort Registry | `ProtocolDeviation` | `Subject` | `log_event`, `irb_review`, `resolve_deviation` |
| `manufacturing` | Assembly Line Quality Control | `NonConformance` | `WorkStation` | `containment`, `root_cause_analysis`, `close` |
| `event_ops` | Global Conference Logistics | `CredentialRequest` | `VenueHall` | `security_screening`, `issue_badge`, `revoke` |
| `finops` | Cloud Infrastructure Cost Allocator | `CostAnomaly` | `CloudAccount` | `triage`, `suppress`, `remediate`, `archive` |
| `municipal` | City Permitting & Inspection | `PermitApplication` | `Parcel` | `plan_review`, `schedule_inspection`, `issue_permit` |
| `media_production` | Studio Asset Pipeline | `VFXShot` | `Scene` | `assign_artist`, `director_review`, `final_composite` |
| `agriculture` | Precision Agronomy Management | `CropBatch` | `FieldParcel` | `seed`, `apply_treatment`, `harvest`, `grade` |
| `legal_tech` | Contract Lifecycle & Discovery | `DiscoveryItem` | `Matter` | `privilege_review`, `redact`, `produce`, `clawback` |
| `maritime` | Port Berthing & Vessel Traffic | `BerthReservation` | `Vessel` | `pilot_assigned`, `docked`, `customs_cleared`, `departed` |
| `aviation` | Flight Dispatch & Ground Handling | `DispatchRelease` | `Aircraft` | `fuel_loaded`, `weight_balance_signed`, `cleared` |
| `energy_grid` | Substation Outage Management | `OutageTicket` | `Substation` | `dispatch_crew`, `isolate_fault`, `restore_power` |
| `museum_archiving` | Curatorial Provenance Registry | `ArtifactLoan` | `Exhibition` | `condition_report`, `curator_signoff`, `return` |
| `venture_capital` | Dealflow & Portfolio Governance | `InvestmentMemo` | `Company` | `partner_pitch`, `due_diligence`, `ic_approval` |
| `telecom` | Fiber Network Circuit Provisioning | `CircuitOrder` | `Node` | `engineering_audit`, `splice_complete`, `activate` |
| `space_ops` | Satellite Telemetry & Mission Control | `PassSchedule` | `GroundStation` | `los_acquisition`, `downlink_payload`, `archive` |

---

## 4. Generalization Split Controls

The environment provides 5 evaluation split regimes:
- `iid`: In-distribution seed variations.
- `new_ui`: Identical domain & schema, novel visual layout family and vocabulary terminology.
- `new_vocab`: Synonymous terms for entities, fields, and actions.
- `new_workflow`: Branched multi-stage lifecycle topologies with intermediate review gates.
- `ood`: Fully unseen holdout domains and random layouts.

---

## 5. Tools & MCP Protocol

Exposed via standard FastMCP:
- `get_application_schema()`
- `search_entities(entity_name, query, status_filter, limit)`
- `get_entity_details(entity_name, entity_id)`
- `create_entity(entity_name, fields_json, actor)`
- `update_entity_fields(entity_name, entity_id, fields_json, actor)`
- `transition_entity_workflow(entity_name, entity_id, action, actor, actor_role, reason)`
- `get_audit_trail(entity_id, limit)`

---

## 6. Verifier & Oracle

- **Layered Verifier**:
  - Layer 1: Target entity final state assertion.
  - Layer 2: Field value modifications.
  - Layer 3: System audit log inspection ensuring sequence integrity and no prohibited actions.
- **Oracle Solver**: BFS state machine pathfinder and trajectory executor achieving 100% ground-truth pass rate across all domains.

---

## 7. Running Tests

```bash
# Run automated test suite
./software/tests/test.sh

# Or directly with pytest
pytest software/tests/ -v
```
