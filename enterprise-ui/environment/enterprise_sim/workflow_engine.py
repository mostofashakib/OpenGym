"""Enterprise workflow engine modeling complex multi-step cross-system processes."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Callable, Dict, List, Optional, Tuple


class WorkflowEngine:
    """State machine orchestrating cross-system enterprise workflows with approval gates."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def start_workflow(
        self,
        workflow_name: str,
        customer_id: str,
        entity_id: str,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initialize a new workflow instance."""
        inst_id = f"wf-{workflow_name[:8]}-{entity_id}-{len(self._get_all_instances()) + 1:04d}"
        data = initial_data or {}
        now_iso = "2026-10-15T09:00:00Z"

        initial_step = "verify_case" if workflow_name == "customer_refund" else "initial_step"

        self.conn.execute(
            """INSERT INTO workflow_instances (
                id, workflow_name, customer_id, entity_id, status, current_step, step_data_json, created_iso, updated_iso
            ) VALUES (?, ?, ?, ?, 'running', ?, ?, ?, ?)""",
            (inst_id, workflow_name, customer_id, entity_id, initial_step, json.dumps(data), now_iso, now_iso),
        )
        self.conn.commit()

        return {
            "instance_id": inst_id,
            "workflow_name": workflow_name,
            "status": "running",
            "current_step": initial_step,
            "data": data,
        }

    def get_workflow_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve state and step data for a workflow instance."""
        row = self.conn.execute(
            "SELECT * FROM workflow_instances WHERE id = ?", (instance_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "workflow_name": row[1],
            "customer_id": row[2],
            "entity_id": row[3],
            "status": row[4],
            "current_step": row[5],
            "step_data": json.loads(row[6]),
            "created_iso": row[7],
            "updated_iso": row[8],
        }

    def advance_step(
        self,
        instance_id: str,
        next_step: str,
        step_outputs: Optional[Dict[str, Any]] = None,
        mark_completed: bool = False,
    ) -> Dict[str, Any]:
        """Transition workflow instance to the next step."""
        wf = self.get_workflow_instance(instance_id)
        if not wf:
            return {"success": False, "error": f"Workflow instance {instance_id} not found."}

        if wf["status"] not in ("running", "blocked"):
            return {"success": False, "error": f"Cannot advance workflow in status '{wf['status']}'."}

        data = wf["step_data"]
        if step_outputs:
            data.update(step_outputs)

        status = "completed" if mark_completed else "running"
        now_iso = "2026-10-15T09:30:00Z"

        self.conn.execute(
            """UPDATE workflow_instances
               SET status = ?, current_step = ?, step_data_json = ?, updated_iso = ?
               WHERE id = ?""",
            (status, next_step, json.dumps(data), now_iso, instance_id),
        )
        self.conn.commit()

        return {
            "success": True,
            "instance_id": instance_id,
            "status": status,
            "current_step": next_step,
            "data": data,
        }

    def block_for_approval(
        self,
        instance_id: str,
        request_id: str,
        current_step: str = "awaiting_approval",
    ) -> Dict[str, Any]:
        """Mark workflow as blocked pending manager approval decision."""
        wf = self.get_workflow_instance(instance_id)
        if not wf:
            return {"success": False, "error": f"Workflow {instance_id} not found."}

        data = wf["step_data"]
        data["pending_approval_id"] = request_id

        self.conn.execute(
            """UPDATE workflow_instances
               SET status = 'blocked', current_step = ?, step_data_json = ?
               WHERE id = ?""",
            (current_step, json.dumps(data), instance_id),
        )
        self.conn.commit()
        return {"success": True, "instance_id": instance_id, "status": "blocked", "current_step": current_step}

    def fail_workflow(self, instance_id: str, reason: str) -> Dict[str, Any]:
        """Mark workflow as failed with logged reason."""
        wf = self.get_workflow_instance(instance_id)
        if not wf:
            return {"success": False, "error": f"Workflow {instance_id} not found."}

        data = wf["step_data"]
        data["failure_reason"] = reason

        self.conn.execute(
            """UPDATE workflow_instances
               SET status = 'failed', step_data_json = ?
               WHERE id = ?""",
            (json.dumps(data), instance_id),
        )
        self.conn.commit()
        return {"success": True, "instance_id": instance_id, "status": "failed", "reason": reason}

    def _get_all_instances(self) -> List[Any]:
        return self.conn.execute("SELECT id FROM workflow_instances").fetchall()
