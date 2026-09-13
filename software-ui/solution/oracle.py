"""Universal Oracle Solver for procedurally generated software environments.

Can solve tasks either by executing ground-truth oracle trajectories directly,
or by inspecting the schema and computing graph paths across workflow states.
"""

from __future__ import annotations

import argparse
import json
import logging
from typing import Any, Dict, List, Optional

from software.tools.software_client import SoftwareClient

logger = logging.getLogger(__name__)


class OracleSolver:
    """Solves tasks in the Software Environment with 100% ground-truth accuracy."""

    def __init__(self, client: SoftwareClient) -> None:
        self.client = client

    def solve_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the solution steps for a given task specification."""
        trajectory = task_spec.get("oracle_trajectory", [])
        executed_steps: List[Dict[str, Any]] = []

        if trajectory:
            for step in trajectory:
                step_type = step.get("step")
                entity_name = step.get("entity")
                entity_id = step.get("id")

                if step_type == "transition":
                    action = step.get("action")
                    actor_role = step.get("role", "admin")
                    res = self.client.transition(
                        entity_name=entity_name,
                        entity_id=entity_id,
                        action=action,
                        actor="oracle_solver",
                        actor_role=actor_role,
                    )
                    executed_steps.append({"step": step, "result": res})

                elif step_type == "update":
                    fields = step.get("fields", {})
                    res = self.client.update(
                        entity_name=entity_name,
                        entity_id=entity_id,
                        fields=fields,
                        actor="oracle_solver",
                    )
                    executed_steps.append({"step": step, "result": res})

                elif step_type == "create":
                    fields = step.get("fields", {})
                    res = self.client.create(
                        entity_name=entity_name,
                        fields=fields,
                        actor="oracle_solver",
                    )
                    executed_steps.append({"step": step, "result": res})

            return {
                "success": True,
                "executed_steps_count": len(executed_steps),
                "steps": executed_steps,
            }

        # Fallback: Automatic state machine pathfinder
        assertions = task_spec.get("assertions", {})
        target_entity = assertions.get("entity_name") or task_spec.get("target_entity")
        target_id = assertions.get("entity_id") or task_spec.get("target_entity_id")
        target_state = assertions.get("expected_state") or task_spec.get("target_state")

        if target_entity and target_id and target_state:
            res = self._solve_by_graph_search(target_entity, target_id, target_state)
            return {
                "success": res.get("success", False),
                "executed_steps_count": len(res.get("steps", [])),
                "steps": res.get("steps", []),
            }

        return {"success": False, "error": "Unable to determine solution path"}

    def _solve_by_graph_search(
        self,
        entity_name: str,
        entity_id: str,
        target_state: str,
    ) -> Dict[str, Any]:
        """BFS search over workflow transitions from current state to target state."""
        record = self.client.get(entity_name, entity_id)
        if not record:
            return {"success": False, "error": f"Record {entity_id} not found"}

        current_state = str(record.get("status") or "")
        if not current_state:
            return {"success": False, "error": f"Record {entity_id} has no status"}
        if current_state == target_state:
            return {"success": True, "steps": []}

        entity_spec = next(
            (e for e in self.client.app_spec.entities if e.name == entity_name),
            None,
        )
        if not entity_spec or not entity_spec.workflow:
            return {"success": False, "error": f"No workflow for {entity_name}"}

        transitions = entity_spec.workflow.transitions

        # BFS to find shortest path of transitions
        queue: List[tuple[str, List[tuple[str, str]]]] = [(current_state, [])]
        visited = {current_state}
        found_path: Optional[List[tuple[str, str]]] = None

        while queue:
            state, path = queue.pop(0)
            if state == target_state:
                found_path = path
                break

            for t in transitions:
                if t.from_state == state and t.to_state not in visited:
                    visited.add(t.to_state)
                    queue.append((t.to_state, path + [(t.action, t.allowed_roles[0] if t.allowed_roles else "admin")]))

        if not found_path:
            return {"success": False, "error": f"No workflow path from {current_state} to {target_state}"}

        executed = []
        for action, role in found_path:
            res = self.client.transition(
                entity_name=entity_name,
                entity_id=entity_id,
                action=action,
                actor="oracle_solver",
                actor_role=role,
            )
            executed.append({"action": action, "role": role, "result": res})

        return {"success": True, "steps": executed}


def main() -> None:
    parser = argparse.ArgumentParser(description="Software Environment Oracle Solver")
    parser.add_argument("--task-file", required=True, help="Task JSON file")
    parser.add_argument("--db-path", default="/tmp/software_sim.db", help="Path to database")
    parser.add_argument("--spec-path", default=None, help="Path to AppSpec JSON")
    args = parser.parse_args()

    with open(args.task_file, "r", encoding="utf-8") as f:
        task_spec = json.load(f)

    client = SoftwareClient(db_path=args.db_path, app_spec_path=args.spec_path)
    solver = OracleSolver(client)
    res = solver.solve_task(task_spec)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
