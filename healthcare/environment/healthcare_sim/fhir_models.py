"""FHIR R4-aligned data models for the Healthcare Agent Simulation Environment."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ClinicalStatus(str, Enum):
    ACTIVE = "active"
    RECURRENCE = "recurrence"
    RELAPSE = "relapse"
    INACTIVE = "inactive"
    REMISSION = "remission"
    RESOLVED = "resolved"


class AllergyCriticality(str, Enum):
    LOW = "low"
    HIGH = "high"
    UNABLE_TO_ASSESS = "unable-to-assess"


class EncounterStatus(str, Enum):
    PLANNED = "planned"
    ARRIVED = "arrived"
    TRIAGED = "triaged"
    IN_PROGRESS = "in-progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class MedicationStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    STOPPED = "stopped"
    DRAFT = "draft"


class ServiceRequestStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    REVOKED = "revoked"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"


class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    ARRIVED = "arrived"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    NOSHOW = "noshow"


@dataclass
class Patient:
    id: str
    mrn: str
    first_name: str
    last_name: str
    gender: str
    birth_date: str  # YYYY-MM-DD
    phone: str = ""
    email: str = ""
    address: str = ""
    active: bool = True
    primary_provider_id: Optional[str] = None
    deceased: bool = False
    is_pregnant: bool = False

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Patient:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Encounter:
    id: str
    patient_id: str
    encounter_type: str  # e.g. "office-visit", "inpatient", "telehealth", "emergency"
    class_code: str = "AMB"  # AMB (ambulatory), IMP (inpatient), EMER (emergency)
    status: str = EncounterStatus.FINISHED.value
    start_iso: str = ""
    end_iso: str = ""
    provider_id: str = ""
    facility_id: str = ""
    reason_code: str = ""
    reason_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Encounter:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Condition:
    id: str
    patient_id: str
    encounter_id: str = ""
    code_icd10: str = ""
    display: str = ""
    clinical_status: str = ClinicalStatus.ACTIVE.value
    verification_status: str = "confirmed"
    onset_iso: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Condition:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MedicationRequest:
    id: str
    patient_id: str
    medication_name: str
    dosage_instruction: str
    status: str = MedicationStatus.ACTIVE.value
    encounter_id: str = ""
    rxnorm_code: str = ""
    route: str = "oral"
    frequency: str = "daily"
    dose_amount: float = 0.0
    dose_unit: str = "mg"
    prescriber_id: str = ""
    authored_on_iso: str = ""
    refills: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> MedicationRequest:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AllergyIntolerance:
    id: str
    patient_id: str
    substance_code: str
    substance_name: str
    category: str = "medication"  # medication, food, environment, biologic
    criticality: str = AllergyCriticality.HIGH.value
    manifestation: str = "anaphylaxis"
    onset_iso: str = ""
    verification_status: str = "confirmed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> AllergyIntolerance:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Observation:
    id: str
    patient_id: str
    category: str  # "vital-signs" or "laboratory"
    code_loinc: str
    display: str
    value_numeric: Optional[float] = None
    value_string: Optional[str] = None
    unit: str = ""
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    interpretation: str = "normal"  # "normal", "high", "low", "critical-high", "critical-low"
    effective_iso: str = ""
    encounter_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Observation:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Procedure:
    id: str
    patient_id: str
    code_cpt: str
    display: str
    status: str = "completed"
    performed_iso: str = ""
    encounter_id: str = ""
    provider_id: str = ""
    consent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Procedure:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Immunization:
    id: str
    patient_id: str
    vaccine_code: str
    vaccine_name: str
    status: str = "completed"
    occurrence_iso: str = ""
    lot_number: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Immunization:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class DocumentReference:
    id: str
    patient_id: str
    doc_type: str  # "progress-note", "consult-note", "imaging-report", "discharge-summary"
    title: str
    author_id: str
    created_iso: str
    content_text: str
    encounter_id: str = ""
    status: str = "final"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> DocumentReference:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class ServiceRequest:
    id: str
    patient_id: str
    service_code: str
    display: str  # e.g., "Cardiology Consultation", "Abdominal Ultrasound"
    intent: str = "order"
    priority: str = "routine"  # "routine", "urgent", "asap", "stat"
    status: str = ServiceRequestStatus.ACTIVE.value
    requester_id: str = ""
    recipient_id: str = ""
    encounter_id: str = ""
    auth_id: Optional[str] = None
    created_iso: str = ""
    reason_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> ServiceRequest:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Appointment:
    id: str
    patient_id: str
    provider_id: str
    facility_id: str
    service_type: str
    status: str = AppointmentStatus.BOOKED.value
    start_iso: str = ""
    end_iso: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Appointment:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Coverage:
    id: str
    patient_id: str
    payer_id: str
    payer_name: str
    subscriber_id: str
    plan_type: str  # "HMO", "PPO", "Medicare", "Medicaid"
    status: str = "active"
    prior_auth_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Coverage:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Consent:
    id: str
    patient_id: str
    consent_type: str  # "treatment", "hipaa-disclosure", "procedure-surgical"
    status: str = "active"  # "active", "rejected", "expired"
    start_iso: str = ""
    end_iso: str = ""
    authorized_roles: List[str] = field(default_factory=lambda: ["physician", "nurse"])
    limitations: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Consent:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Communication:
    id: str
    sender_type: str  # "patient" or "staff"
    sender_id: str
    recipient_type: str  # "patient" or "staff"
    recipient_id: str
    patient_id: str
    subject: str
    body: str
    sent_iso: str
    status: str = "completed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Communication:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class CareTeam:
    id: str
    patient_id: str
    name: str
    status: str = "active"
    participant_practitioner_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> CareTeam:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Practitioner:
    id: str
    name: str
    role: str  # "physician", "nurse", "medical_assistant", "billing_specialist", "scheduler", "pharmacist", "admin_staff"
    department: str  # "primary_care", "cardiology", "endocrinology", "orthopedics", "billing", "pharmacy"
    clinic_facility_id: str
    npi: str
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> Practitioner:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
