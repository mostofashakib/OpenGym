"""Automatic graph-based task generator with verified ground truth solutions."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from .spec import AppSpec


def generate_task_from_graph(
    db_path: Path | str,
    spec: AppSpec,
) -> dict[str, Any]:
    """Generate a multi-step task with ground truth solution from the database graph."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # Find primary workflow entity
        primary_wf = spec.workflows[0]
        ent_name = primary_wf.entity_name
        ent = next((e for e in spec.entities if e.name == ent_name), None)
        if not ent:
            raise ValueError(f"Entity '{ent_name}' not found in AppSpec.")

        # Check if there are numeric fields like 'days_delayed' or 'urgency' or 'credits'
        numeric_fields = [f.name for f in ent.fields if "delay" in f.name or "cost" in f.name or "hour" in f.name]
        filter_col = numeric_fields[0] if numeric_fields else None

        if filter_col:
            # Task pattern: Filter entities exceeding threshold, resolve exceptions/blockers, and transition state
            query = f"SELECT * FROM {ent_name} WHERE {filter_col} >= 2 LIMIT 5"
            rows = conn.execute(query).fetchall()
            if not rows:
                query = f"SELECT * FROM {ent_name} LIMIT 5"
                rows = conn.execute(query).fetchall()
        else:
            query = f"SELECT * FROM {ent_name} LIMIT 5"
            rows = conn.execute(query).fetchall()

        target_records = [dict(r) for r in rows]
        target_ids = [r[ent.primary_key] for r in target_records]

        # Look for first valid transition from current states
        current_state = target_records[0].get("status", primary_wf.initial_state) if target_records else primary_wf.initial_state
        available_transition = next((t for t in primary_wf.transitions if t.from_state == current_state), primary_wf.transitions[0])

        action_name = available_transition.name
        expected_state = available_transition.to_state

        prompt = (
            f"You are working in {spec.name} ({spec.domain}).\n\n"
            f"Your objective:\n"
            f"1. Query the {ent.plural_name} registry using `search_entities`.\n"
            f"2. Identify the {len(target_ids)} target records requiring attention: {', '.join(target_ids)}.\n"
            f"3. For each identified record, execute the workflow action `{action_name}` to transition its lifecycle status to `{expected_state}`.\n"
            f"4. Ensure all dependent records or activity logs are maintained."
        )

        oracle_steps = []
        for tid in target_ids:
            oracle_steps.append({
                "tool": "transition_entity",
                "arguments": {
                    "entity_name": ent_name,
                    "entity_id": tid,
                    "action": action_name,
                },
            })

        return {
            "task_id": f"task_{spec.domain}_{spec.seed}",
            "domain": spec.domain,
            "prompt": prompt,
            "target_entity": ent_name,
            "target_ids": target_ids,
            "action_name": action_name,
            "expected_state": expected_state,
            "oracle_steps": oracle_steps,
        }
    finally:
        conn.close()


class TaskGenerator:
    """Generates synthetic tasks and ground-truth oracle trajectories from database state."""

    def __init__(self, app_spec: AppSpec, db_path: Path | str, seed: int = 42) -> None:
        self.app_spec = app_spec
        self.db_path = db_path
        self.seed = seed

    def generate_task(self) -> dict[str, Any]:
        raw_task = generate_task_from_graph(self.db_path, self.app_spec)
        raw_task["instruction"] = raw_task["prompt"]
        raw_task["oracle_trajectory"] = [
            {
                "step": "transition",
                "entity": step["arguments"]["entity_name"],
                "id": step["arguments"]["entity_id"],
                "action": step["arguments"]["action"],
                "role": "admin",
            }
            for step in raw_task.get("oracle_steps", [])
        ]
        first_target = raw_task["target_ids"][0] if raw_task.get("target_ids") else ""
        raw_task["assertions"] = {
            "entity_name": raw_task["target_entity"],
            "entity_id": first_target,
            "expected_state": raw_task["expected_state"],
            "all_target_ids": raw_task["target_ids"],
        }
        return raw_task

