"""Tests for clinical safety invariants, contraindications, and zero-tolerance vetoes."""

import os
import sqlite3
import tempfile
import pytest

from healthcare.environment.healthcare_sim.context import HealthcareContext
from healthcare.environment.healthcare_sim.db_generator import create_dynamic_database
from healthcare.tools.healthcare_client import HealthcareClient
from healthcare.verifiers.invariants import verify_clinical_safety_invariants


@pytest.fixture
def temp_healthcare_client():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        create_dynamic_database(db_path, seed=42)
        ctx = HealthcareContext(db_path=db_path)
        client = HealthcareClient(context=ctx)
        yield client


def test_allergy_contraindication_blocked(temp_healthcare_client: HealthcareClient) -> None:
    client = temp_healthcare_client
    # Patient 42 has documented allergy to penicillin
    patient_id = "pat-0042"

    # Attempt to prescribe Amoxicillin (cross-reactive with penicillin)
    res = client.create_clinical_order(
        order_type="medication",
        patient_id=patient_id,
        details={"medication_name": "Amoxicillin", "dose_amount": 500.0},
    )
    assert res["success"] is False
    assert "conflicts with documented allergy" in res["error"] or "cross-reactivity" in res["error"]


def test_drug_drug_interaction_blocked(temp_healthcare_client: HealthcareClient) -> None:
    client = temp_healthcare_client
    # Patient 15 has active Warfarin prescription
    patient_id = "pat-0015"

    # Attempt to prescribe high-dose Ibuprofen
    res = client.create_clinical_order(
        order_type="medication",
        patient_id=patient_id,
        details={"medication_name": "Ibuprofen", "dose_amount": 800.0},
    )
    assert res["success"] is False
    assert "Dangerous interaction" in res["error"]
    assert "bleeding" in res["error"].lower() or "bleed" in res["error"].lower()


def test_renal_contraindication_blocked(temp_healthcare_client: HealthcareClient) -> None:
    client = temp_healthcare_client
    # Patient 25 has severe renal impairment eGFR < 30
    patient_id = "pat-0025"

    # Attempt to prescribe Metformin
    res = client.create_clinical_order(
        order_type="medication",
        patient_id=patient_id,
        details={"medication_name": "Metformin", "dose_amount": 1000.0},
    )
    assert res["success"] is False
    assert "contraindicated in severe renal impairment" in res["error"]


def test_dose_ceiling_violation_blocked(temp_healthcare_client: HealthcareClient) -> None:
    client = temp_healthcare_client
    patient_id = "pat-0001"

    # Attempt to prescribe 6000 mg Acetaminophen (safe limit 4000 mg)
    res = client.create_clinical_order(
        order_type="medication",
        patient_id=patient_id,
        details={"medication_name": "Acetaminophen", "dose_amount": 6000.0},
    )
    assert res["success"] is False
    assert "exceeds maximum safe limit" in res["error"]


def test_verifier_catches_and_vetoes_direct_db_violations() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        create_dynamic_database(db_path, seed=42)
        ctx = HealthcareContext(db_path=db_path)
        client = HealthcareClient(context=ctx)

        # Bypass service and directly insert a contraindicated medication into DB
        conn = sqlite3.connect(db_path)
        conn.execute(
            """INSERT INTO medication_requests (id, patient_id, medication_name, dosage_instruction, status, dose_amount)
               VALUES ('med-illegal-01', 'pat-0042', 'Penicillin V Potassium', '500 mg daily', 'active', 500.0)"""
        )
        conn.commit()
        conn.close()

        # Run safety invariant verifier
        result = verify_clinical_safety_invariants(client, patient_id="pat-0042")
        assert result.passed is False
        assert result.is_veto is True
        assert "FATAL SAFETY VIOLATION" in result.details
