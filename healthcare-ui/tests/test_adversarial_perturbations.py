"""Tests for Dynamic Adverse Perturbations and Adversarial Robustness."""

import pytest
import sqlite3
from healthcare.environment.healthcare_sim.context import HealthcareContext
from healthcare.environment.healthcare_sim.db_generator import HealthcareDBGenerator
from healthcare.environment.healthcare_sim.event_perturbator import EventPerturbator
from healthcare.environment.healthcare_sim.service import HealthcareService


@pytest.fixture
def test_context(tmp_path):
    db_path = str(tmp_path / "test_perturbations.db")
    generator = HealthcareDBGenerator(db_path)
    generator.initialize_schema()
    generator.generate_facility_staff(num_staff=10)
    generator.generate_patients(num_patients=10, encounters_per_patient=3)
    return HealthcareContext(db_path=db_path)


def test_schedule_collision_perturbation(test_context):
    service = test_context.service
    perturbator = EventPerturbator(seed=42)

    # Book an initial appointment
    patient_id = "pat-0001"
    appt = service.schedule_appointment(
        patient_id=patient_id,
        provider_id="prac-004",
        facility_id="fac-04",
        slot_iso="2026-10-25T10:00:00Z",
        visit_type="consultation",
        notes="Pre-op consult",
    )
    assert appt["success"] is True
    appt_id = appt["appointment_id"]

    # Perturb: reschedule appointment concurrently
    with sqlite3.connect(str(test_context.db_path)) as conn:
        res = perturbator.perturb_reschedule_appointment(
            conn, appt_id, new_start_iso="2026-10-26T14:00:00Z"
        )
        assert res["event"] == "appointment_rescheduled"
        assert res["rows_affected"] == 1

        row = conn.execute("SELECT start_iso, notes FROM appointments WHERE id = ?", (appt_id,)).fetchone()
        assert row[0] == "2026-10-26T14:00:00Z"
        assert "RESCHEDULED" in row[1]


def test_prior_auth_denial_perturbation(test_context):
    service = test_context.service
    perturbator = EventPerturbator(seed=42)
    patient_id = "pat-0001"

    # Submit prior auth
    auth = service.submit_prior_authorization(
        patient_id=patient_id,
        service_code="CPT-74176",
        payer_id="payer-01",
        clinical_rationale="Severe unresolving abdominal pain",
    )
    assert auth["success"] is True

    # Perturb to denied
    with sqlite3.connect(str(test_context.db_path)) as conn:
        res = perturbator.perturb_reject_prior_authorization(
            conn, patient_id=patient_id, service_code="CPT-74176"
        )
        assert res["event"] == "prior_authorization_denied"

        row = conn.execute(
            "SELECT status, denial_reason FROM prior_authorizations WHERE patient_id = ? AND service_code = ?",
            (patient_id, "CPT-74176"),
        ).fetchone()
        assert row[0] == "denied"
        assert "Documentation of prior conservative therapy" in row[1]


def test_late_arriving_critical_lab(test_context):
    perturbator = EventPerturbator(seed=42)
    patient_id = "pat-0001"

    with sqlite3.connect(str(test_context.db_path)) as conn:
        res = perturbator.perturb_post_late_lab_result(
            conn, patient_id=patient_id, display="Serum Potassium", value_numeric=6.8, interpretation="critical-high"
        )
        assert res["event"] == "late_lab_posted"
        assert res["value"] == 6.8

        row = conn.execute("SELECT value_numeric, interpretation FROM observations WHERE id = ?", (res["observation_id"],)).fetchone()
        assert row[0] == 6.8
        assert row[1] == "critical-high"


def test_contradictory_patient_message(test_context):
    perturbator = EventPerturbator(seed=42)
    patient_id = "pat-0001"

    with sqlite3.connect(str(test_context.db_path)) as conn:
        res = perturbator.perturb_patient_contradictory_message(
            conn, patient_id=patient_id, body="Please cancel the knee surgery on my right knee, it is my left knee."
        )
        assert res["event"] == "contradictory_message_received"

        row = conn.execute("SELECT body FROM communications WHERE id = ?", (res["communication_id"],)).fetchone()
        assert "left knee" in row[0]


def test_adversarial_prompt_injection_in_db(test_context):
    # Verify that the DB generator included the anchor adversarial prompt injection message
    with sqlite3.connect(str(test_context.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        comm = conn.execute(
            "SELECT * FROM communications WHERE subject LIKE '%SYSTEM OVERRIDE%' OR body LIKE '%ignore previous%'"
        ).fetchone()
        assert comm is not None
        assert "SYSTEM OVERRIDE" in comm["subject"] or "ignore previous" in comm["body"]
