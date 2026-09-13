"""Tests for FHIR R4-aligned data models and serialization."""

from healthcare.environment.healthcare_sim.fhir_models import (
    AllergyIntolerance,
    Appointment,
    Condition,
    Encounter,
    MedicationRequest,
    Observation,
    Patient,
    Practitioner,
    ServiceRequest,
)


def test_patient_model() -> None:
    pat = Patient(
        id="pat-0001",
        mrn="MRN000001",
        first_name="John",
        last_name="Smith",
        gender="male",
        birth_date="1980-05-20",
    )
    assert pat.full_name == "John Smith"
    d = pat.to_dict()
    assert d["mrn"] == "MRN000001"
    reconstructed = Patient.from_dict(d)
    assert reconstructed.id == pat.id
    assert reconstructed.birth_date == "1980-05-20"


def test_medication_and_allergy_models() -> None:
    med = MedicationRequest(
        id="med-01",
        patient_id="pat-0001",
        medication_name="Amoxicillin",
        dosage_instruction="500 mg oral three times daily",
        dose_amount=500.0,
        dose_unit="mg",
    )
    assert med.dose_amount == 500.0

    allergy = AllergyIntolerance(
        id="all-01",
        patient_id="pat-0001",
        substance_code="penicillin",
        substance_name="penicillin",
        criticality="high",
        manifestation="anaphylaxis",
    )
    assert allergy.criticality == "high"
    assert allergy.manifestation == "anaphylaxis"


def test_observation_model() -> None:
    obs = Observation(
        id="obs-01",
        patient_id="pat-0001",
        category="laboratory",
        code_loinc="33914-3",
        display="eGFR",
        value_numeric=22.5,
        unit="mL/min/1.73m2",
        interpretation="low",
        effective_iso="2026-10-15T08:00:00Z",
    )
    assert obs.value_numeric == 22.5
    assert obs.interpretation == "low"
