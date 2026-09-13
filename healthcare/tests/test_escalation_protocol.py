"""Tests for Human-in-the-Loop Clinical Escalation Protocol."""

import pytest
from healthcare.environment.healthcare_sim.context import HealthcareContext
from healthcare.environment.healthcare_sim.db_generator import HealthcareDBGenerator
from healthcare.environment.healthcare_sim.service import HealthcareService
from healthcare.environment.healthcare_sim.invariants import SafetyInvariantEngine


@pytest.fixture
def test_context(tmp_path):
    db_path = str(tmp_path / "test_escalation.db")
    generator = HealthcareDBGenerator(db_path)
    generator.initialize_schema()
    generator.generate_facility_staff(num_staff=5)
    generator.generate_patients(num_patients=5, encounters_per_patient=2)
    return HealthcareContext(db_path=db_path)


def test_triage_emergency_symptoms():
    engine = SafetyInvariantEngine()

    # Chest pain
    is_flagged, symptoms = engine.check_red_flag_symptoms_in_text(
        "Patient reports severe crushing chest pain radiating to left arm and jaw"
    )
    assert is_flagged
    assert any("chest pain" in s for s in symptoms)

    # Stroke symptoms
    is_flagged, symptoms = engine.check_red_flag_symptoms_in_text(
        "Sudden facial droop and right-sided hemiparesis, slurred speech"
    )
    assert is_flagged
    assert any("facial droop" in s or "slurred speech" in s for s in symptoms)

    # Normal non-urgent symptom
    is_flagged, symptoms = engine.check_red_flag_symptoms_in_text("Mild toe stiffness after jogging")
    assert not is_flagged
    assert len(symptoms) == 0


def test_triage_panic_lab_values():
    engine = SafetyInvariantEngine()

    # Critical high potassium
    is_critical, msg = engine.is_critical_lab_value("potassium", 6.8)
    assert is_critical
    assert "Critical High" in msg

    # Normal potassium
    is_critical, msg = engine.is_critical_lab_value("potassium", 4.2)
    assert not is_critical

    # Critical low blood glucose
    is_critical, msg = engine.is_critical_lab_value("blood glucose", 35.0)
    assert is_critical
    assert "Critical Low" in msg


def test_service_escalate_emergency(test_context):
    service = HealthcareService(test_context)
    patient_id = "pat-0001"

    res = service.escalate_to_human_clinician(
        patient_id=patient_id,
        urgency="emergency",
        clinical_summary="Patient reports sudden onset dyspnea and crushing substernal chest pain",
        required_action="Transfer to Emergency Department immediately",
        actor_id="prac-001",
        actor_role="nurse",
    )

    assert res["success"] is True
    assert res["urgency"] == "emergency"
    assert res["status"] == "open"
    assert res["patient_id"] == patient_id

    # Verify audit event was logged
    audit_events = service.get_audit_log(patient_id=patient_id)
    assert len(audit_events) >= 1
    assert any(ev.get("action") == "escalate" for ev in audit_events)
