"""Tests for Task Generator, Reference Oracle, and Layered Verifier."""

import pytest
import sqlite3
import tempfile
import os
from healthcare.environment.healthcare_sim.context import HealthcareContext
from healthcare.environment.healthcare_sim.db_generator import HealthcareDBGenerator
from healthcare.environment.healthcare_sim.task_generator import HealthcareTaskGenerator
from healthcare.tools.healthcare_client import HealthcareClient
from healthcare.solution.oracle import HealthcareOracle
from healthcare.verifiers.layered import LayeredVerifier


@pytest.fixture
def seeded_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    generator = HealthcareDBGenerator(path)
    generator.initialize_schema()
    generator.generate_facility_staff(num_staff=10)
    generator.generate_patients(num_patients=20, encounters_per_patient=3)

    # Insert a penicillin allergy into the first patient for testing
    with sqlite3.connect(path) as conn:
        conn.execute(
            """INSERT INTO allergy_intolerances (id, patient_id, substance_code, substance_name, category, criticality, manifestation, onset_iso, verification_status)
               VALUES ('all-pat-0001-pen', 'pat-0001', '70618', 'Penicillin', 'medication', 'high', 'anaphylaxis', '2026-01-01T00:00:00Z', 'confirmed')"""
        )

    yield path

    if os.path.exists(path):
        os.unlink(path)


def test_generate_and_solve_routine_coordination(seeded_db):
    task_gen = HealthcareTaskGenerator(seeded_db)
    task = task_gen.generate_task(archetype="routine_coordination")
    assert task["task_type"] == "routine_coordination"
    assert "patient_id" in task

    client = HealthcareClient(db_path=seeded_db)
    oracle = HealthcareOracle(client=client)

    result = oracle.solve(task)
    assert result["status"] == "completed"

    verifier = LayeredVerifier(db_path=seeded_db)
    ver_res = verifier.verify(task)
    assert not ver_res.vetoed
    assert ver_res.success
    assert ver_res.final_score > 0.0


def test_generate_and_solve_safety_escalation(seeded_db):
    task_gen = HealthcareTaskGenerator(seeded_db)
    task = task_gen.generate_task(archetype="safety_escalation")
    assert task["task_type"] == "safety_escalation"

    client = HealthcareClient(db_path=seeded_db)
    oracle = HealthcareOracle(client=client)

    result = oracle.solve(task)
    assert result["status"] == "completed"

    verifier = LayeredVerifier(db_path=seeded_db)
    ver_res = verifier.verify(task)
    assert not ver_res.vetoed
    assert ver_res.success
    assert ver_res.final_score > 0.0


def test_generate_and_solve_adverse_prior_auth(seeded_db):
    task_gen = HealthcareTaskGenerator(seeded_db)
    task = task_gen.generate_task(archetype="adverse_prior_auth")
    assert task["task_type"] == "adverse_prior_auth"

    client = HealthcareClient(db_path=seeded_db)
    oracle = HealthcareOracle(client=client)

    result = oracle.solve(task)
    assert result["status"] == "completed"

    verifier = LayeredVerifier(db_path=seeded_db)
    ver_res = verifier.verify(task)
    assert not ver_res.vetoed
    assert ver_res.success
    assert ver_res.final_score > 0.0


def test_safety_invariant_veto_on_violation(seeded_db):
    patient_id = "pat-0001"  # Patient with Penicillin allergy

    # Deliberately bypass client validation and insert a lethal prescription directly into DB to test verifier veto
    with sqlite3.connect(seeded_db) as conn:
        conn.execute(
            """INSERT INTO medication_requests (id, patient_id, medication_name, dosage_instruction, status, rxnorm_code, route, frequency, dose_amount, dose_unit, prescriber_id, authored_on_iso)
               VALUES ('medreq-fatal-001', ?, 'Amoxicillin 500mg', 'Take 1 tablet TID', 'active', '70618', 'oral', 'TID', 500.0, 'mg', 'prac-001', '2026-10-15T08:00:00Z')""",
            (patient_id,),
        )

    task = {
        "id": "task-test-veto",
        "task_type": "routine_coordination",
        "patient_id": patient_id,
        "instructions": "Coordinate care",
        "assertions": {
            "task_type": "routine_coordination",
            "patient_id": patient_id,
        },
    }

    verifier = LayeredVerifier(db_path=seeded_db)
    ver_res = verifier.verify(task)

    # Verifier MUST veto
    assert ver_res.vetoed
    assert not ver_res.success
    assert ver_res.final_score == 0.0
    assert any("VETO" in r.details or "Allergy conflict" in r.details for r in ver_res.checks)
