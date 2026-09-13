"""Tool definitions and schemas for the Healthcare Agent Simulation Environment."""

from __future__ import annotations

from typing import Any, Dict, List

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "verify_patient_identity",
        "description": "Verify patient demographic identifiers (name, DOB, MRN) before initiating chart access or orders.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient ID (e.g. 'pat-0001')"},
                "first_name": {"type": "string", "description": "First name to verify"},
                "last_name": {"type": "string", "description": "Last name to verify"},
                "birth_date": {"type": "string", "description": "DOB in YYYY-MM-DD format"},
                "mrn": {"type": "string", "description": "Medical Record Number (e.g. 'MRN000001')"},
            },
            "required": ["patient_id"],
        },
    },
    {
        "name": "get_patient_chart",
        "description": "Retrieve comprehensive longitudinal patient chart sections (conditions, medications, allergies, observations, encounters, referrals, appointments, documents).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient ID"},
                "section_filter": {
                    "type": "string",
                    "description": "Optional chart section filter (e.g. 'medications', 'allergies', 'observations', 'referrals')",
                },
            },
            "required": ["patient_id"],
        },
    },
    {
        "name": "search_clinical_records",
        "description": "Search across clinical tables (patients, conditions, medications, observations, procedures, appointments, referrals).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "Resource type to query"},
                "patient_id": {"type": "string", "description": "Optional patient ID filter"},
                "query_json": {"type": "string", "description": "JSON object of column-value filters"},
            },
            "required": ["resource_type"],
        },
    },
    {
        "name": "create_clinical_order",
        "description": "Create a clinical prescription order, lab diagnostic order, or specialty referral.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_type": {"type": "string", "enum": ["medication", "diagnostic", "referral"]},
                "patient_id": {"type": "string", "description": "Target patient ID"},
                "details_json": {"type": "string", "description": "JSON object specifying order parameters"},
            },
            "required": ["order_type", "patient_id", "details_json"],
        },
    },
    {
        "name": "update_order_or_referral",
        "description": "Update the lifecycle status or notes of an existing service request or referral.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Service request or referral order ID"},
                "status": {"type": "string", "description": "New status (e.g. 'active', 'completed', 'on-hold', 'revoked')"},
                "notes": {"type": "string", "description": "Clinical justification or update notes"},
            },
            "required": ["order_id", "status"],
        },
    },
    {
        "name": "schedule_appointment",
        "description": "Book a clinic appointment slot with a designated provider and facility.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient ID"},
                "provider_id": {"type": "string", "description": "Practitioner ID"},
                "facility_id": {"type": "string", "description": "Clinic facility ID"},
                "slot_iso": {"type": "string", "description": "Appointment start ISO timestamp"},
                "visit_type": {"type": "string", "description": "Visit type (e.g. 'consultation', 'pre-op-lab', 'follow-up')"},
                "notes": {"type": "string", "description": "Scheduling notes"},
            },
            "required": ["patient_id", "provider_id", "facility_id", "slot_iso"],
        },
    },
    {
        "name": "send_portal_message",
        "description": "Send a secure message to a patient or clinical care team member.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipient_type": {"type": "string", "enum": ["patient", "staff"]},
                "recipient_id": {"type": "string", "description": "ID of recipient"},
                "patient_id": {"type": "string", "description": "Subject patient ID"},
                "subject": {"type": "string", "description": "Message subject"},
                "body": {"type": "string", "description": "Message text"},
            },
            "required": ["recipient_type", "recipient_id", "patient_id", "subject", "body"],
        },
    },
    {
        "name": "submit_prior_authorization",
        "description": "Submit a prior authorization coverage request to an insurance payer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient ID"},
                "service_code": {"type": "string", "description": "CPT or procedure code requiring authorization"},
                "payer_id": {"type": "string", "description": "Insurance payer ID"},
                "clinical_rationale": {"type": "string", "description": "Medical necessity rationale"},
            },
            "required": ["patient_id", "service_code", "payer_id", "clinical_rationale"],
        },
    },
    {
        "name": "escalate_to_human_clinician",
        "description": "Handoff a case to an authorized physician when clinical safety thresholds or emergency symptoms are detected.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Patient ID"},
                "urgency": {"type": "string", "enum": ["routine", "urgent", "emergency"]},
                "clinical_summary": {"type": "string", "description": "Synthesized summary of safety conflict or clinical urgency"},
                "required_action": {"type": "string", "description": "Requested physician action"},
            },
            "required": ["patient_id", "urgency", "clinical_summary", "required_action"],
        },
    },
    {
        "name": "get_audit_log",
        "description": "Retrieve audit trail of chart access, disclosures, and orders.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string", "description": "Optional patient filter"},
                "limit": {"type": "integer", "description": "Max events to return (default 50)"},
            },
        },
    },
]
