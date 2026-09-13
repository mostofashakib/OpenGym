"""Library of 20 diverse, realistic domain templates for generative software applications."""

from __future__ import annotations

from typing import Any

from .spec import (
    AppSpec,
    EntitySpec,
    FieldSpec,
    FieldType,
    RelationshipSpec,
    RelationType,
    RoleSpec,
    UILayoutFamily,
    UILayoutSpec,
    WorkflowSpec,
    WorkflowTransition,
)


def _common_roles() -> tuple[RoleSpec, ...]:
    return (
        RoleSpec(name="admin", description="Full system access", permissions=("all",)),
        RoleSpec(name="manager", description="Department supervisor", permissions=("read", "write", "transition")),
        RoleSpec(name="operator", description="Standard frontline staff", permissions=("read", "write")),
        RoleSpec(name="auditor", description="Read-only compliance officer", permissions=("read",)),
    )


# ---------------------------------------------------------------------------
# Domain 1: Logistics & Freight
# ---------------------------------------------------------------------------
def get_logistics_template(seed: int = 42) -> AppSpec:
    entities = (
        EntitySpec(
            name="Shipment",
            plural_name="Shipments",
            description="Consolidated freight cargo moving through network depots",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="tracking_number", field_type=FieldType.STRING),
                FieldSpec(name="depot_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Depot"),
                FieldSpec(name="driver_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Driver"),
                FieldSpec(name="weight_kg", field_type=FieldType.FLOAT, default=150.0),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=("booked", "in_transit", "delayed", "out_for_delivery", "delivered")),
                FieldSpec(name="days_delayed", field_type=FieldType.INTEGER, default=0),
                FieldSpec(name="origin", field_type=FieldType.STRING),
                FieldSpec(name="destination", field_type=FieldType.STRING),
            ),
            lifecycle_states=("booked", "in_transit", "delayed", "out_for_delivery", "delivered"),
        ),
        EntitySpec(
            name="Depot",
            plural_name="Depots",
            description="Regional sorting and dispatch center",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="code", field_type=FieldType.STRING),
                FieldSpec(name="city", field_type=FieldType.STRING),
                FieldSpec(name="capacity_teu", field_type=FieldType.INTEGER, default=500),
                FieldSpec(name="manager_name", field_type=FieldType.STRING),
            ),
        ),
        EntitySpec(
            name="Driver",
            plural_name="Drivers",
            description="Commercial transport operator",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="name", field_type=FieldType.STRING),
                FieldSpec(name="license_class", field_type=FieldType.STRING, default="Class A"),
                FieldSpec(name="assigned_depot_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Depot"),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=("active", "off_duty", "in_route")),
            ),
            lifecycle_states=("active", "off_duty", "in_route"),
        ),
        EntitySpec(
            name="Exception",
            plural_name="Exceptions",
            description="Transit interruption or delay incident log",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="shipment_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Shipment"),
                FieldSpec(name="reason", field_type=FieldType.STRING),
                FieldSpec(name="severity", field_type=FieldType.ENUM, enum_values=("low", "medium", "critical")),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=("open", "investigating", "cleared")),
                FieldSpec(name="resolution_notes", field_type=FieldType.TEXT, default=""),
            ),
            lifecycle_states=("open", "investigating", "cleared"),
        ),
    )

    workflows = (
        WorkflowSpec(
            entity_name="Shipment",
            initial_state="booked",
            terminal_states=("delivered",),
            transitions=(
                WorkflowTransition(name="dispatch", from_state="booked", to_state="in_transit", required_roles=("admin", "manager")),
                WorkflowTransition(name="flag_delay", from_state="in_transit", to_state="delayed", required_roles=("admin", "operator")),
                WorkflowTransition(name="reroute", from_state="delayed", to_state="in_transit", required_roles=("admin", "manager")),
                WorkflowTransition(name="out_for_delivery", from_state="in_transit", to_state="out_for_delivery", required_roles=("admin", "operator")),
                WorkflowTransition(name="confirm_delivery", from_state="out_for_delivery", to_state="delivered", required_roles=("admin", "operator")),
            ),
        ),
        WorkflowSpec(
            entity_name="Exception",
            initial_state="open",
            terminal_states=("cleared",),
            transitions=(
                WorkflowTransition(name="investigate", from_state="open", to_state="investigating", required_roles=("admin", "operator")),
                WorkflowTransition(name="clear_exception", from_state="investigating", to_state="cleared", required_roles=("admin", "manager")),
            ),
        ),
    )

    relationships = (
        RelationshipSpec(source_entity="Depot", target_entity="Shipment", relation_type=RelationType.ONE_TO_MANY, foreign_key_name="depot_id"),
        RelationshipSpec(source_entity="Driver", target_entity="Shipment", relation_type=RelationType.ONE_TO_MANY, foreign_key_name="driver_id"),
        RelationshipSpec(source_entity="Shipment", target_entity="Exception", relation_type=RelationType.ONE_TO_MANY, foreign_key_name="shipment_id"),
    )

    layout = UILayoutSpec(
        layout_family=UILayoutFamily.SIDEBAR_TABLE,
        terminology_map={"Shipment": "Consignment", "Exception": "Transit Issue"},
        visible_columns={"Shipment": ("id", "tracking_number", "status", "days_delayed", "destination")},
        filter_fields={"Shipment": ("status", "depot_id")},
    )

    return AppSpec(
        name="LogiFlow Enterprise Freight",
        domain="logistics",
        description="Global supply-chain cargo dispatch, exception resolution, and depot network monitoring",
        seed=seed,
        entities=entities,
        workflows=workflows,
        relationships=relationships,
        roles=_common_roles(),
        layout=layout,
    )


# ---------------------------------------------------------------------------
# Domain 2: Higher Education & University Registrar
# ---------------------------------------------------------------------------
def get_registrar_template(seed: int = 42) -> AppSpec:
    entities = (
        EntitySpec(
            name="Student",
            plural_name="Students",
            description="Enrolled matriculated scholar",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="full_name", field_type=FieldType.STRING),
                FieldSpec(name="major", field_type=FieldType.STRING),
                FieldSpec(name="gpa", field_type=FieldType.FLOAT, default=3.5),
                FieldSpec(name="academic_standing", field_type=FieldType.ENUM, enum_values=("good", "probation", "honors")),
            ),
        ),
        EntitySpec(
            name="Course",
            plural_name="Courses",
            description="Curriculum lecture offering",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="course_code", field_type=FieldType.STRING),
                FieldSpec(name="title", field_type=FieldType.STRING),
                FieldSpec(name="credits", field_type=FieldType.INTEGER, default=3),
                FieldSpec(name="capacity", field_type=FieldType.INTEGER, default=30),
                FieldSpec(name="enrolled_count", field_type=FieldType.INTEGER, default=0),
            ),
        ),
        EntitySpec(
            name="OverrideRequest",
            plural_name="OverrideRequests",
            description="Prerequisite or capacity waiver petition",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="student_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Student"),
                FieldSpec(name="course_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Course"),
                FieldSpec(name="reason", field_type=FieldType.TEXT),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=("submitted", "faculty_review", "dean_review", "approved", "rejected")),
            ),
            lifecycle_states=("submitted", "faculty_review", "dean_review", "approved", "rejected"),
        ),
    )

    workflows = (
        WorkflowSpec(
            entity_name="OverrideRequest",
            initial_state="submitted",
            terminal_states=("approved", "rejected"),
            transitions=(
                WorkflowTransition(name="submit_to_faculty", from_state="submitted", to_state="faculty_review", required_roles=("operator", "admin")),
                WorkflowTransition(name="escalate_to_dean", from_state="faculty_review", to_state="dean_review", required_roles=("manager", "admin")),
                WorkflowTransition(name="approve", from_state="dean_review", to_state="approved", required_roles=("admin", "manager")),
                WorkflowTransition(name="reject", from_state="faculty_review", to_state="rejected", required_roles=("manager", "admin")),
                WorkflowTransition(name="reject_dean", from_state="dean_review", to_state="rejected", required_roles=("admin",)),
            ),
        ),
    )

    relationships = (
        RelationshipSpec(source_entity="Student", target_entity="OverrideRequest", relation_type=RelationType.ONE_TO_MANY, foreign_key_name="student_id"),
        RelationshipSpec(source_entity="Course", target_entity="OverrideRequest", relation_type=RelationType.ONE_TO_MANY, foreign_key_name="course_id"),
    )

    layout = UILayoutSpec(
        layout_family=UILayoutFamily.NESTED_TREE_CARDS,
        terminology_map={"OverrideRequest": "Petition", "Course": "Lecture Module"},
    )

    return AppSpec(
        name="Campus Registrar Suite",
        domain="higher_ed",
        description="University course enrollment, prerequisite overrides, and degree audit workflows",
        seed=seed,
        entities=entities,
        workflows=workflows,
        relationships=relationships,
        roles=_common_roles(),
        layout=layout,
    )


# ---------------------------------------------------------------------------
# Domain 3: Heavy Equipment Maintenance
# ---------------------------------------------------------------------------
def get_equipment_template(seed: int = 42) -> AppSpec:
    entities = (
        EntitySpec(
            name="Asset",
            plural_name="Assets",
            description="Industrial plant machinery or heavy construction vehicle",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="serial_no", field_type=FieldType.STRING),
                FieldSpec(name="model", field_type=FieldType.STRING),
                FieldSpec(name="operating_hours", field_type=FieldType.FLOAT, default=1250.0),
                FieldSpec(name="operational_status", field_type=FieldType.ENUM, enum_values=("operational", "degraded", "offline")),
            ),
            lifecycle_states=("operational", "degraded", "offline"),
        ),
        EntitySpec(
            name="WorkOrder",
            plural_name="WorkOrders",
            description="Scheduled or emergency maintenance ticket",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="asset_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Asset"),
                FieldSpec(name="urgency", field_type=FieldType.ENUM, enum_values=("standard", "urgent", "critical")),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=("draft", "assigned", "parts_hold", "in_progress", "completed")),
                FieldSpec(name="technician_id", field_type=FieldType.STRING),
                FieldSpec(name="work_summary", field_type=FieldType.TEXT, default=""),
            ),
            lifecycle_states=("draft", "assigned", "parts_hold", "in_progress", "completed"),
        ),
        EntitySpec(
            name="PartInventory",
            plural_name="PartInventories",
            description="Spare component catalog item",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="part_number", field_type=FieldType.STRING),
                FieldSpec(name="quantity_available", field_type=FieldType.INTEGER, default=10),
                FieldSpec(name="unit_cost_usd", field_type=FieldType.FLOAT, default=45.0),
            ),
        ),
    )

    workflows = (
        WorkflowSpec(
            entity_name="WorkOrder",
            initial_state="draft",
            terminal_states=("completed",),
            transitions=(
                WorkflowTransition(name="assign_tech", from_state="draft", to_state="assigned", required_roles=("manager", "admin")),
                WorkflowTransition(name="hold_for_parts", from_state="assigned", to_state="parts_hold", required_roles=("operator", "admin")),
                WorkflowTransition(name="release_parts", from_state="parts_hold", to_state="in_progress", required_roles=("manager", "admin")),
                WorkflowTransition(name="start_work", from_state="assigned", to_state="in_progress", required_roles=("operator", "admin")),
                WorkflowTransition(name="complete_order", from_state="in_progress", to_state="completed", required_roles=("operator", "manager")),
            ),
        ),
    )

    relationships = (
        RelationshipSpec(source_entity="Asset", target_entity="WorkOrder", relation_type=RelationType.ONE_TO_MANY, foreign_key_name="asset_id"),
    )

    layout = UILayoutSpec(
        layout_family=UILayoutFamily.SPLIT_WORKSPACE,
        terminology_map={"WorkOrder": "Job Card", "Asset": "Machinery Unit"},
    )

    return AppSpec(
        name="PlantCare Machinery Maintenance",
        domain="equipment",
        description="Preventive maintenance, asset uptime tracking, and work order assignment",
        seed=seed,
        entities=entities,
        workflows=workflows,
        relationships=relationships,
        roles=_common_roles(),
        layout=layout,
    )


# ---------------------------------------------------------------------------
# Domain 4: Scientific Research & Lab Management
# ---------------------------------------------------------------------------
def get_research_template(seed: int = 42) -> AppSpec:
    entities = (
        EntitySpec(
            name="Experiment",
            plural_name="Experiments",
            description="Laboratory hypothesis protocol execution",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="title", field_type=FieldType.STRING),
                FieldSpec(name="lead_scientist", field_type=FieldType.STRING),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=("designed", "ethics_approved", "running", "peer_review", "published")),
            ),
            lifecycle_states=("designed", "ethics_approved", "running", "peer_review", "published"),
        ),
        EntitySpec(
            name="Sample",
            plural_name="Samples",
            description="Biological or chemical reagent specimen",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="experiment_id", field_type=FieldType.FOREIGN_KEY, foreign_entity="Experiment"),
                FieldSpec(name="barcode", field_type=FieldType.STRING),
                FieldSpec(name="storage_freezer", field_type=FieldType.STRING, default="Freezer-80C-B"),
                FieldSpec(name="is_depleted", field_type=FieldType.BOOLEAN, default=False),
            ),
        ),
    )

    workflows = (
        WorkflowSpec(
            entity_name="Experiment",
            initial_state="designed",
            terminal_states=("published",),
            transitions=(
                WorkflowTransition(name="approve_ethics", from_state="designed", to_state="ethics_approved", required_roles=("manager", "admin")),
                WorkflowTransition(name="launch_run", from_state="ethics_approved", to_state="running", required_roles=("operator", "admin")),
                WorkflowTransition(name="submit_review", from_state="running", to_state="peer_review", required_roles=("manager", "admin")),
                WorkflowTransition(name="publish_results", from_state="peer_review", to_state="published", required_roles=("admin",)),
            ),
        ),
    )

    relationships = (
        RelationshipSpec(source_entity="Experiment", target_entity="Sample", relation_type=RelationType.ONE_TO_MANY, foreign_key_name="experiment_id"),
    )

    layout = UILayoutSpec(
        layout_family=UILayoutFamily.TABBED_BOARD,
        terminology_map={"Experiment": "Study", "Sample": "Specimen"},
    )

    return AppSpec(
        name="BioLab Horizon Research",
        domain="research",
        description="Scientific assay tracking, specimen storage, and peer review publishing pipeline",
        seed=seed,
        entities=entities,
        workflows=workflows,
        relationships=relationships,
        roles=_common_roles(),
        layout=layout,
    )


# ---------------------------------------------------------------------------
# Additional Domains Generator (Domains 5 to 20)
# ---------------------------------------------------------------------------
ADDITIONAL_DOMAINS = [
    ("real_estate", "Commercial Property Hub", "Property", "Properties", "Lease", "Leases", ("draft", "negotiation", "active", "expired")),
    ("clinical_trials", "ClinTrack Trial OS", "Trial", "Trials", "Participant", "Participants", ("screened", "enrolled", "active", "completed")),
    ("manufacturing", "Apex Factory Mesh", "ProductionBatch", "ProductionBatches", "QualityCheck", "QualityChecks", ("queued", "milling", "inspecting", "shipped")),
    ("event_ops", "Summiteer Conference Suite", "Session", "Sessions", "AttendeeRegistration", "Registrations", ("registered", "checked_in", "cancelled")),
    ("finops", "CloudLedger Cost Allocation", "CloudAccount", "CloudAccounts", "AnomalyAlert", "AnomalyAlerts", ("flagged", "triaged", "suppressed", "resolved")),
    ("municipal", "Metro Permitting & Zoning", "ZoningApplication", "ZoningApplications", "Permit", "Permits", ("filed", "hearing_scheduled", "approved", "denied")),
    ("media_production", "FrameHouse Render Studio", "Project", "Projects", "RenderJob", "RenderJobs", ("queued", "rendering", "review", "delivered")),
    ("agriculture", "CropYield Fleet Monitor", "FieldPlot", "FieldPlots", "CropBatch", "CropBatches", ("growing", "harvesting", "stored", "distributed")),
    ("legal_tech", "LexisCore Matter Nexus", "Matter", "Matters", "Deposition", "Depositions", ("scheduled", "recorded", "transcribed", "sealed")),
    ("maritime", "Oceania Port Terminal", "Vessel", "Vessels", "CustomsDeclaration", "Declarations", ("lodged", "inspected", "cleared", "detained")),
    ("aviation", "AeroTurn Ground Handling", "FlightTurn", "FlightTurns", "DeicingLog", "DeicingLogs", ("scheduled", "treatment_active", "cleared_for_takeoff")),
    ("energy_grid", "PowerGrid Dispatch Grid", "SolarFarm", "SolarFarms", "CurtailmentEvent", "Curtailments", ("monitoring", "alert", "curtailed", "restored")),
    ("museum_archiving", "CuratorVault Artifacts", "Artwork", "Artworks", "LoanContract", "LoanContracts", ("draft", "approved", "active", "returned")),
    ("venture_capital", "Syndicate DealFlow", "StartupLead", "StartupLeads", "TermSheet", "TermSheets", ("sourced", "partner_review", "signed", "passed")),
    ("telecom", "FiberGrid Fiber Network", "PermitRoute", "PermitRoutes", "NodeActivation", "NodeActivations", ("surveyed", "splicing", "testing", "live")),
    ("space_ops", "GroundOrbit Satellite Operations", "GroundStation", "GroundStations", "OrbitalPass", "OrbitalPasses", ("scheduled", "tracking", "downlinked", "lost")),
]


def _build_generic_domain(domain_key: str, seed: int) -> AppSpec:
    info = next((d for d in ADDITIONAL_DOMAINS if d[0] == domain_key), None)
    if not info:
        return get_logistics_template(seed)

    _, title, e1, e1_pl, e2, e2_pl, states = info

    transitions: list[WorkflowTransition] = []
    for i in range(len(states) - 1):
        transitions.append(
            WorkflowTransition(
                name=f"advance_{states[i]}_to_{states[i+1]}",
                from_state=states[i],
                to_state=states[i+1],
                required_roles=("admin", "manager"),
            )
        )

    entities = (
        EntitySpec(
            name=e1,
            plural_name=e1_pl,
            description=f"Primary record in {title}",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="name", field_type=FieldType.STRING),
                FieldSpec(name="code", field_type=FieldType.STRING),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=states),
            ),
            lifecycle_states=states,
        ),
        EntitySpec(
            name=e2,
            plural_name=e2_pl,
            description=f"Operational item associated with {e1}",
            fields=(
                FieldSpec(name="id", field_type=FieldType.STRING),
                FieldSpec(name="parent_id", field_type=FieldType.FOREIGN_KEY, foreign_entity=e1),
                FieldSpec(name="title", field_type=FieldType.STRING),
                FieldSpec(name="status", field_type=FieldType.ENUM, enum_values=("pending", "active", "resolved")),
            ),
            lifecycle_states=("pending", "active", "resolved"),
        ),
    )

    workflows = (
        WorkflowSpec(
            entity_name=e1,
            initial_state=states[0],
            terminal_states=(states[-1],),
            transitions=tuple(transitions),
        ),
    )

    relationships = (
        RelationshipSpec(source_entity=e1, target_entity=e2, relation_type=RelationType.ONE_TO_MANY, foreign_key_name="parent_id"),
    )

    layout = UILayoutSpec(
        layout_family=UILayoutFamily.SIDEBAR_TABLE,
        terminology_map={e1: e1.upper()},
    )

    entities = _link_workflows(entities, workflows)
    return AppSpec(
        name=title,
        domain=domain_key,
        description=f"Declarative software environment for {title}",
        seed=seed,
        entities=entities,
        workflows=workflows,
        relationships=relationships,
        roles=_common_roles(),
        layout=layout,
    )


def _link_workflows(entities: tuple[EntitySpec, ...], workflows: tuple[WorkflowSpec, ...]) -> tuple[EntitySpec, ...]:
    wf_map = {w.entity_name: w for w in workflows}
    linked = []
    for ent in entities:
        wf = wf_map.get(ent.name)
        if wf:
            linked.append(EntitySpec(
                name=ent.name,
                plural_name=ent.plural_name,
                description=ent.description,
                fields=ent.fields,
                lifecycle_states=ent.lifecycle_states,
                primary_key=ent.primary_key,
                workflow=wf,
            ))
        else:
            linked.append(ent)
    return tuple(linked)


ALL_DOMAIN_KEYS = [
    "logistics", "higher_ed", "equipment", "research",
    "real_estate", "clinical_trials", "manufacturing", "event_ops",
    "finops", "municipal", "media_production", "agriculture",
    "legal_tech", "maritime", "aviation", "energy_grid",
    "museum_archiving", "venture_capital", "telecom", "space_ops"
]

DOMAIN_REGISTRY: dict[str, str] = {k: k for k in ALL_DOMAIN_KEYS}


def get_domain_template(domain_key: str, seed: int = 42) -> AppSpec:
    if domain_key == "logistics":
        spec = get_logistics_template(seed)
    elif domain_key == "higher_ed":
        spec = get_registrar_template(seed)
    elif domain_key == "equipment":
        spec = get_equipment_template(seed)
    elif domain_key == "research":
        spec = get_research_template(seed)
    else:
        spec = _build_generic_domain(domain_key, seed)

    # Ensure workflows are linked
    linked_entities = _link_workflows(spec.entities, spec.workflows)
    return AppSpec(
        name=spec.name,
        domain=spec.domain,
        description=spec.description,
        seed=spec.seed,
        entities=linked_entities,
        workflows=spec.workflows,
        relationships=spec.relationships,
        roles=spec.roles,
        layout=spec.layout,
    )


def get_domain_spec(domain_key: str, seed: int = 42) -> AppSpec:
    """Retrieve domain specification by key."""
    return get_domain_template(domain_key, seed=seed)


def get_all_domains() -> list[str]:
    """List all registered domain template keys."""
    return list(ALL_DOMAIN_KEYS)

