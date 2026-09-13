"""Abstract state machine execution engine and transition validator."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .spec import AppSpec, WorkflowSpec, WorkflowTransition


class WorkflowError(Exception):
    """Error during state transition validation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StateMachineEngine:
    """Validates and executes lifecycle transitions across declarative entities."""

    def __init__(self, spec: AppSpec) -> None:
        self.spec = spec
        self.workflows_by_entity: dict[str, WorkflowSpec] = {
            w.entity_name: w for w in spec.workflows
        }

    def can_transition(
        self,
        entity_name: str,
        current_state: str,
        action_name: str,
        actor_role: str = "admin",
    ) -> tuple[bool, str | None, WorkflowTransition | None]:
        """Check if an entity can transition via action_name."""
        wf = self.workflows_by_entity.get(entity_name)
        if not wf:
            return False, f"Entity '{entity_name}' has no defined workflow state machine.", None

        transition = next(
            (t for t in wf.transitions if t.from_state == current_state and t.name == action_name),
            None,
        )
        if not transition:
            allowed = [t.name for t in wf.transitions if t.from_state == current_state]
            return False, f"Invalid transition '{action_name}' from state '{current_state}'. Allowed: {allowed}", None

        if actor_role not in transition.required_roles and "all" not in transition.required_roles:
            return False, f"Role '{actor_role}' does not have permission for transition '{action_name}'. Required: {transition.required_roles}", None

        return True, None, transition

    def execute_transition(
        self,
        conn: sqlite3.Connection,
        entity_name: str,
        entity_id: str,
        action_name: str,
        actor: str = "user_01",
        actor_role: str = "admin",
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Validate and apply a state transition to an entity in the database."""
        row = conn.execute(f"SELECT * FROM {entity_name} WHERE id = ?", (entity_id,)).fetchone()
        if not row:
            raise WorkflowError("not_found", f"Entity '{entity_name}' with ID '{entity_id}' not found.")

        current_state = str(row["status"])
        can_do, err_msg, trans = self.can_transition(entity_name, current_state, action_name, actor_role)
        if not can_do or not trans:
            raise WorkflowError("invalid_transition", err_msg or "Transition rejected.")

        to_state = trans.to_state
        update_cols = ["status = ?"]
        params: list[Any] = [to_state]

        # Apply any additional field updates
        if fields:
            for k, v in fields.items():
                if k not in ("id", "status"):
                    update_cols.append(f"{k} = ?")
                    params.append(v)

        params.append(entity_id)
        sql = f"UPDATE {entity_name} SET {', '.join(update_cols)} WHERE id = ?"
        conn.execute(sql, tuple(params))

        # Log transition into action_logs
        ts_row = conn.execute("SELECT value FROM system_state WHERE key = 'virtual_time_iso'").fetchone()
        now_iso = str(ts_row[0]) if ts_row else "2026-10-14T09:00:00Z"

        conn.execute(
            """INSERT INTO action_logs (timestamp_iso, actor, entity_name, action, entity_id, from_state, to_state, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (now_iso, actor, entity_name, action_name, entity_id, current_state, to_state, json.dumps(fields or {})),
        )

        return {
            "entity_name": entity_name,
            "entity_id": entity_id,
            "action": action_name,
            "from_state": current_state,
            "to_state": to_state,
            "updated_fields": fields or {},
        }
