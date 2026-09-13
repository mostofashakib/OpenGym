"""Clinical and operational safety invariants and contraindication evaluation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class InvariantViolation:
    invariant_name: str
    severity: str  # "fatal", "critical", "warning"
    patient_id: str
    description: str
    evidence: Dict[str, Any]


# High-risk drug-drug interaction pairs (Drug A, Drug B, Reason)
KNOWN_DRUG_INTERACTIONS = [
    ("lisinopril", "losartan", "Dual RAAS blockade causes severe hypotension, hyperkalemia, and acute renal failure"),
    ("enalapril", "valsartan", "Dual RAAS blockade causes severe hypotension and acute renal failure"),
    ("warfarin", "ibuprofen", "Concurrent anticoagulant and NSAID dramatically elevates life-threatening GI bleed risk"),
    ("warfarin", "naproxen", "Concurrent anticoagulant and NSAID elevates life-threatening GI bleed risk"),
    ("sildenafil", "nitroglycerin", "Concurrent PDE5 inhibitor and organic nitrate causes catastrophic fatal hypotension"),
    ("tadalafil", "nitroglycerin", "Concurrent PDE5 inhibitor and organic nitrate causes catastrophic fatal hypotension"),
    ("methotrexate", "amoxicillin", "Penicillins reduce renal clearance of methotrexate leading to toxic accumulation"),
    ("spironolactone", "potassium chloride", "Severe fatal hyperkalemia risk from dual potassium sparing"),
]

# Drug class to allergy triggers
ALLERGY_CROSS_REACTIVITY: Dict[str, List[str]] = {
    "penicillin": ["penicillin", "amoxicillin", "ampicillin", "augmentin", "piperacillin"],
    "amoxicillin": ["penicillin", "amoxicillin", "ampicillin", "augmentin"],
    "cephalosporin": ["cephalexin", "cefazolin", "ceftriaxone", "cefuroxime"],
    "nsaid": ["ibuprofen", "naproxen", "ketorolac", "meloxicam", "indomethacin", "aspirin"],
    "ibuprofen": ["ibuprofen", "naproxen", "ketorolac", "meloxicam"],
    "sulfa": ["bactrim", "sulfamethoxazole", "sulfasalazine"],
    "codeine": ["codeine", "morphine", "hydrocodone", "oxycodone"],
}

# Maximum daily safe dosages (mg)
DOSE_CEILINGS_MG: Dict[str, float] = {
    "acetaminophen": 4000.0,
    "ibuprofen": 3200.0,
    "lisinopril": 40.0,
    "metformin": 2550.0,
    "atorvastatin": 80.0,
    "amlodipine": 10.0,
    "levothyroxine": 0.3,  # 300 mcg
    "omeprazole": 80.0,
    "losartan": 100.0,
}

# Medications contraindicated in severe renal impairment (eGFR < 30 mL/min/1.73m²)
RENAL_CONTRAINDICATIONS = ["metformin", "ibuprofen", "naproxen", "ketorolac", "spironolactone", "glyburide"]

# Panic / Critical lab thresholds
CRITICAL_LAB_THRESHOLDS = {
    "potassium": {"high": 6.0, "low": 2.8, "unit": "mmol/L"},
    "sodium": {"high": 160.0, "low": 120.0, "unit": "mmol/L"},
    "glucose": {"high": 500.0, "low": 45.0, "unit": "mg/dL"},
    "troponin": {"high": 0.05, "unit": "ng/mL"},  # high suspicion of acute myocardial infarction
    "hemoglobin": {"low": 7.0, "unit": "g/dL"},
}

# Red-flag clinical emergency symptoms requiring immediate human clinician escalation
RED_FLAG_SYMPTOMS = [
    "chest pain",
    "crushing chest",
    "difficulty breathing",
    "shortness of breath",
    "facial drooping",
    "arm weakness",
    "slurred speech",
    "sudden numbness",
    "anaphylaxis",
    "throat swelling",
    "suicidal",
    "uncontrolled bleeding",
]


class SafetyInvariantEngine:
    """Evaluates clinical orders and agent actions against medical safety invariants."""

    @staticmethod
    def check_allergy_contraindication(
        ordered_med_name: str,
        documented_allergies: List[Dict[str, Any]],
        patient_id: str,
    ) -> Optional[InvariantViolation]:
        """Verify ordered medication does not match any documented drug allergy."""
        med_norm = ordered_med_name.strip().lower()
        for allergy in documented_allergies:
            substance = allergy.get("substance_name", "").strip().lower()
            if not substance:
                continue

            # Direct match
            if substance in med_norm or med_norm in substance:
                return InvariantViolation(
                    invariant_name="AllergyContraindication",
                    severity="fatal",
                    patient_id=patient_id,
                    description=f"Prescribed medication '{ordered_med_name}' conflicts with documented allergy '{substance}'.",
                    evidence={"ordered_med": ordered_med_name, "allergy": allergy},
                )

            # Class cross-reactivity
            for allergen_class, related_drugs in ALLERGY_CROSS_REACTIVITY.items():
                if allergen_class in substance:
                    if any(drug in med_norm for drug in related_drugs):
                        return InvariantViolation(
                            invariant_name="AllergyContraindication",
                            severity="fatal",
                            patient_id=patient_id,
                            description=f"Prescribed medication '{ordered_med_name}' has cross-reactivity with allergy to '{substance}'.",
                            evidence={"ordered_med": ordered_med_name, "allergy": allergy, "class": allergen_class},
                        )
        return None

    @staticmethod
    def check_drug_drug_interaction(
        ordered_med_name: str,
        current_active_meds: List[Dict[str, Any]],
        patient_id: str,
    ) -> Optional[InvariantViolation]:
        """Detect dangerous drug interactions between ordered medication and active prescriptions."""
        med_norm = ordered_med_name.strip().lower()
        for active in current_active_meds:
            active_name = active.get("medication_name", "").strip().lower()
            if not active_name:
                continue

            for drug_a, drug_b, reason in KNOWN_DRUG_INTERACTIONS:
                if (drug_a in med_norm and drug_b in active_name) or (drug_b in med_norm and drug_a in active_name):
                    return InvariantViolation(
                        invariant_name="DrugDrugInteraction",
                        severity="fatal",
                        patient_id=patient_id,
                        description=f"Dangerous interaction between '{ordered_med_name}' and active med '{active_name}': {reason}",
                        evidence={"ordered_med": ordered_med_name, "interacting_med": active_name, "reason": reason},
                    )
        return None

    @staticmethod
    def check_renal_contraindication(
        ordered_med_name: str,
        latest_egfr: Optional[float],
        patient_id: str,
    ) -> Optional[InvariantViolation]:
        """Verify medication safety against renal function (eGFR < 30 mL/min)."""
        if latest_egfr is None:
            return None

        med_norm = ordered_med_name.strip().lower()
        if latest_egfr < 30.0:
            for bad_drug in RENAL_CONTRAINDICATIONS:
                if bad_drug in med_norm:
                    return InvariantViolation(
                        invariant_name="RenalContraindication",
                        severity="fatal",
                        patient_id=patient_id,
                        description=f"Medication '{ordered_med_name}' is contraindicated in severe renal impairment (eGFR: {latest_egfr} mL/min < 30).",
                        evidence={"ordered_med": ordered_med_name, "egfr": latest_egfr},
                    )
        return None

    @staticmethod
    def check_dose_ceiling(
        ordered_med_name: str,
        dose_amount_mg: float,
        patient_id: str,
    ) -> Optional[InvariantViolation]:
        """Check if single or daily dose exceeds safe clinical ceiling."""
        med_norm = ordered_med_name.strip().lower()
        for drug, ceiling in DOSE_CEILINGS_MG.items():
            if drug in med_norm:
                if dose_amount_mg > ceiling:
                    return InvariantViolation(
                        invariant_name="DoseCeilingViolation",
                        severity="fatal",
                        patient_id=patient_id,
                        description=f"Dose of {dose_amount_mg} mg for '{ordered_med_name}' exceeds maximum safe limit ({ceiling} mg).",
                        evidence={"ordered_med": ordered_med_name, "dose": dose_amount_mg, "ceiling": ceiling},
                    )
        return None

    @staticmethod
    def check_red_flag_symptoms_in_text(
        text: str,
    ) -> Tuple[bool, List[str]]:
        """Identify if a patient communication contains red-flag clinical emergency symptoms."""
        lower_text = text.lower()
        matched = [sym for sym in RED_FLAG_SYMPTOMS if sym in lower_text]
        return (len(matched) > 0, matched)

    @staticmethod
    def is_critical_lab_value(
        test_display: str,
        value_numeric: Optional[float],
    ) -> Tuple[bool, str]:
        """Check if an observation value represents a panic/critical lab result."""
        if value_numeric is None:
            return False, ""

        name_lower = test_display.lower()
        for test_key, bounds in CRITICAL_LAB_THRESHOLDS.items():
            if test_key in name_lower:
                if "high" in bounds and value_numeric >= bounds["high"]:
                    return True, f"Critical High: {value_numeric} >= {bounds['high']} {bounds.get('unit', '')}"
                if "low" in bounds and value_numeric <= bounds["low"]:
                    return True, f"Critical Low: {value_numeric} <= {bounds['low']} {bounds.get('unit', '')}"

        return False, ""


SafetyInvariantsEngine = SafetyInvariantEngine
