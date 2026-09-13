"""Reference Oracle Solver for the Enterprise Simulation Platform."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from enterprise.tools.enterprise_client import EnterpriseClient


class EnterpriseOracleSolver:
    """Solves cross-system enterprise workflows with 100% adherence to policies and business goals."""

    def __init__(self, client: EnterpriseClient) -> None:
        self.client = client

    def solve_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ground-truth trajectory or compute sound workflow actions."""
        trajectory = task_spec.get("oracle_trajectory", [])
        executed_steps: List[Dict[str, Any]] = []

        if trajectory:
            for step in trajectory:
                tool_name = step.get("tool")
                args = step.get("arguments", {})

                if tool_name == "get_customer_profile":
                    res = self.client.get_customer_profile(customer_id=args.get("customer_id", ""))
                    executed_steps.append({"tool": tool_name, "result": {"has_customer": "customer" in res}})

                elif tool_name == "support_get_ticket":
                    res = self.client.support_get_ticket(ticket_id=args.get("ticket_id", ""))
                    executed_steps.append({"tool": tool_name, "result": {"has_ticket": "ticket" in res}})

                elif tool_name == "workflow_request_approval":
                    res = self.client.workflow_request_approval(
                        request_type=args.get("request_type", "refund_approval"),
                        approver_id=args.get("approver_id", "emp-002"),
                        amount_usd=float(args.get("amount_usd", 0.0)),
                        reason=args.get("reason", ""),
                        workflow_instance_id=args.get("workflow_instance_id"),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "simulate_manager_approval":
                    res = self.client.simulate_manager_approval(approver_id=args.get("approver_id", "emp-002"))
                    executed_steps.append({"tool": tool_name, "result": {"approved_count": len(res)}})

                elif tool_name == "billing_process_refund":
                    res = self.client.billing_process_refund(
                        invoice_id=args.get("invoice_id", ""),
                        customer_id=args.get("customer_id", ""),
                        amount_usd=float(args.get("amount_usd", 0.0)),
                        reason=args.get("reason", ""),
                        approved_by_id=args.get("approved_by_id"),
                        workflow_instance_id=args.get("workflow_instance_id"),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "support_add_comment":
                    res = self.client.support_add_comment(
                        ticket_id=args.get("ticket_id", ""),
                        content=args.get("content", ""),
                        is_internal=args.get("is_internal", False),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "support_update_ticket_status":
                    res = self.client.support_update_ticket_status(
                        ticket_id=args.get("ticket_id", ""),
                        status=args.get("status", "resolved"),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

                elif tool_name == "email_send_message":
                    res = self.client.email_send_message(
                        sender_email=args.get("sender_email", ""),
                        recipient_emails=args.get("recipient_emails", []),
                        subject=args.get("subject", ""),
                        body=args.get("body", ""),
                        cc_emails=args.get("cc_emails"),
                    )
                    executed_steps.append({"tool": tool_name, "result": res})

            return {
                "success": True,
                "status": "completed",
                "executed_steps_count": len(executed_steps),
                "steps": executed_steps,
            }

        return {"success": False, "status": "failed", "error": "No trajectory defined for task."}

    solve = solve_task


EnterpriseOracle = EnterpriseOracleSolver


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise Simulation Oracle Solver")
    parser.add_argument("--task-file", required=True, help="Task JSON specification")
    parser.add_argument("--db-path", default="/var/lib/enterprise/company.db")
    args = parser.parse_args()

    with open(args.task_file, "r", encoding="utf-8") as f:
        task_spec = json.load(f)

    client = EnterpriseClient(db_path=args.db_path)
    solver = EnterpriseOracleSolver(client)
    res = solver.solve_task(task_spec)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
