"""Reference Oracle Solver for the Healthcare Simulation Environment."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional

from healthcare.tools.healthcare_client import HealthcareClient


class HealthcareOracleSolver:
    """Solves healthcare tasks with 100% adherence to clinical safety, privacy, and escalation rules."""

    def __init__(self, client: HealthcareClient) -> None:
        self.client = client

    def solve_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ground-truth trajectory or compute clinically sound workflow actions."""
        trajectory = task_spec.get("oracle_trajectory", [])
        executed_steps: List[Dict[str, Any]] = []

        if trajectory:
            for step in trajectory:
                tool_name = step.get("tool")
                args = step.get("arguments", {})

                if tool_name == "verify_patient_identity":
                    res = self.client.verify_patient_identity(
                        patient_id=args.get("patient_id", ""),
                        first_name=args.get("first_name"),
                        last_name=args.get("last_name"),
                        birth_date=args.get("birth_date"),
                        mrn=args.get("mrn"),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "get_patient_chart":
                    res = self.client.get_patient_chart(
                        patient_id=args.get("patient_id", ""),
                        section_filter=args.get("section_filter"),
                    )
                    executed_steps.append({"tool": tool_name, "result": {"sections": list(res.keys())}})

                elif tool_name == "create_clinical_order":
                    details_json = args.get("details_json", "{}")
                    details = json.loads(details_json) if isinstance(details_json, str) else details_json
                    res = self.client.create_clinical_order(
                        order_type=args.get("order_type", "diagnostic"),
                        patient_id=args.get("patient_id", ""),
                        details=details,
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "schedule_appointment":
                    res = self.client.schedule_appointment(
                        patient_id=args.get("patient_id", ""),
                        provider_id=args.get("provider_id", ""),
                        facility_id=args.get("facility_id", ""),
                        slot_iso=args.get("slot_iso", ""),
                        visit_type=args.get("visit_type", "consultation"),
                        notes=args.get("notes", ""),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "update_order_or_referral":
                    res = self.client.update_order_or_referral(
                        order_id=args.get("order_id", ""),
                        status=args.get("status", "active"),
                        notes=args.get("notes", ""),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "send_portal_message":
                    res = self.client.send_portal_message(
                        recipient_type=args.get("recipient_type", "patient"),
                        recipient_id=args.get("recipient_id", ""),
                        patient_id=args.get("patient_id", ""),
                        subject=args.get("subject", ""),
                        body=args.get("body", ""),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "submit_prior_authorization":
                    res = self.client.submit_prior_authorization(
                        patient_id=args.get("patient_id", ""),
                        service_code=args.get("service_code", ""),
                        payer_id=args.get("payer_id", "payer-01"),
                        clinical_rationale=args.get("clinical_rationale", ""),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "escalate_to_human_clinician":
                    res = self.client.escalate_to_human_clinician(
                        patient_id=args.get("patient_id", ""),
                        urgency=args.get("urgency", "emergency"),
                        clinical_summary=args.get("clinical_summary", ""),
                        required_action=args.get("required_action", ""),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

            return {
                "success": True,
                "status": "completed",
                "executed_steps_count": len(executed_steps),
                "steps": executed_steps,
            }

        return {"success": False, "status": "failed", "error": "No trajectory or strategy defined for task"}

    solve = solve_task


HealthcareOracle = HealthcareOracleSolver



def main() -> None:
    parser = argparse.ArgumentParser(description="Healthcare Simulation Oracle Solver")
    parser.add_argument("--task-file", required=True, help="Task JSON")
    parser.add_argument("--db-path", default="/tmp/healthcare_sim.db")
    args = parser.parse_args()

    with open(args.task_file, "r", encoding="utf-8") as f:
        task_spec = json.load(f)

    client = HealthcareClient(db_path=args.db_path)
    solver = HealthcareOracleSolver(client)
    res = solver.solve_task(task_spec)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
