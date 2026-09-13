"""Universal service layer for interacting with any procedurally generated software application."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from .db_generator import calculate_database_hash
from .engine import StateMachineEngine, WorkflowError
from .spec import (
    AppSpec,
    EntitySpec,
    FieldSpec,
    FieldType,
    RelationshipSpec,
    RelationType,
    RoleSpec,
    UILayoutFamily,
    UILayoutSpec,
    WorkflowSpec,
    WorkflowTransition,
)


def _connect(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _load_app_spec(conn: sqlite3.Connection) -> AppSpec:
    row = conn.execute("SELECT value FROM system_state WHERE key = 'spec_json'").fetchone()
    if not row:
        raise ValueError("Database missing system_state.spec_json")
    raw = json.loads(row[0])

    entities = tuple(
        EntitySpec(
            name=e["name"],
            plural_name=e["plural_name"],
            description=e["description"],
            fields=tuple(
                FieldSpec(
                    name=f["name"],
                    field_type=FieldType(f["type"]),
                    required=f.get("required", True),
                    default=f.get("default"),
                    enum_values=tuple(f.get("enum_values", ())),
                    foreign_entity=f.get("foreign_entity"),
                    description=f.get("description", ""),
                )
                for f in e["fields"]
            ),
            lifecycle_states=tuple(e.get("lifecycle_states", ())),
            primary_key=e.get("primary_key", "id"),
        )
        for e in raw["entities"]
    )

    workflows = tuple(
        WorkflowSpec(
            entity_name=w["entity_name"],
            initial_state=w["initial_state"],
            terminal_states=tuple(w["terminal_states"]),
            transitions=tuple(
                WorkflowTransition(
                    name=t["name"],
                    from_state=t["from_state"],
                    to_state=t["to_state"],
                    required_roles=tuple(t.get("required_roles", ())),
                    required_fields=tuple(t.get("required_fields", ())),
                    prerequisite_conditions=t.get("prerequisite_conditions", {}),
                    description=t.get("description", ""),
                )
                for t in w["transitions"]
            ),
        )
        for w in raw["workflows"]
    )

    relationships = tuple(
        RelationshipSpec(
            source_entity=r["source_entity"],
            target_entity=r["target_entity"],
            relation_type=RelationType(r["relation_type"]),
            foreign_key_name=r["foreign_key_name"],
            description=r.get("description", ""),
        )
        for r in raw["relationships"]
    )

    roles = tuple(
        RoleSpec(name=r["name"], description=r["description"], permissions=tuple(r["permissions"]))
        for r in raw.get("roles", ())
    )

    layout_dict = raw.get("layout", {})
    layout = UILayoutSpec(
        layout_family=UILayoutFamily(layout_dict.get("layout_family", "sidebar_table")),
        terminology_map=layout_dict.get("terminology_map", {}),
        visible_columns=layout_dict.get("visible_columns", {}),
        filter_fields=layout_dict.get("filter_fields", {}),
        pagination_size=layout_dict.get("pagination_size", 25),
    )

    return AppSpec(
        name=raw["name"],
        domain=raw["domain"],
        description=raw["description"],
        seed=raw["seed"],
        entities=entities,
        workflows=workflows,
        relationships=relationships,
        roles=roles,
        layout=layout,
    )


def get_schema(db_path: Path | str) -> dict[str, Any]:
    """Retrieve complete declarative schema, layout, and entities of the generated app."""
    with _connect(db_path) as conn:
        spec = _load_app_spec(conn)
        return spec.as_dict()


def search_entities(
    db_path: Path | str,
    entity_name: str,
    query: str = "",
    filters: dict[str, Any] | None = None,
    sort_by: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    """Query, filter, and paginate records of a given entity type."""
    with _connect(db_path) as conn:
        spec = _load_app_spec(conn)
        ent = next((e for e in spec.entities if e.name.lower() == entity_name.lower()), None)
        if not ent:
            raise ValueError(f"Unknown entity '{entity_name}'.")

        table_name = ent.name
        where_clauses: list[str] = []
        params: list[Any] = []

        if filters:
            for col, val in filters.items():
                if val is not None:
                    where_clauses.append(f"{col} = ?")
                    params.append(val)

        if query:
            text_cols = [f.name for f in ent.fields if f.field_type in (FieldType.STRING, FieldType.TEXT)]
            if text_cols:
                q_clauses = [f"{c} LIKE ?" for c in text_cols]
                where_clauses.append(f"({' OR '.join(q_clauses)})")
                for _ in text_cols:
                    params.append(f"%{query}%")

        where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        order_sql = f" ORDER BY {sort_by}" if sort_by else f" ORDER BY {ent.primary_key} ASC"
        offset = max(0, (page - 1) * page_size)
        limit_sql = f" LIMIT {page_size} OFFSET {offset}"

        count_sql = f"SELECT COUNT(*) FROM {table_name}{where_sql}"
        total_count = conn.execute(count_sql, tuple(params[: len(params) - (len(params) - len(where_clauses)) if not query else len(params)])).fetchone()[0]

        data_sql = f"SELECT * FROM {table_name}{where_sql}{order_sql}{limit_sql}"
        rows = conn.execute(data_sql, tuple(params)).fetchall()

        return {
            "entity_name": ent.name,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        }


def get_entity(
    db_path: Path | str,
    entity_name: str,
    entity_id: str,
) -> dict[str, Any]:
    """Retrieve a single entity record by ID, along with related child records."""
    with _connect(db_path) as conn:
        spec = _load_app_spec(conn)
        ent = next((e for e in spec.entities if e.name.lower() == entity_name.lower()), None)
        if not ent:
            raise ValueError(f"Unknown entity '{entity_name}'.")

        row = conn.execute(f"SELECT * FROM {ent.name} WHERE {ent.primary_key} = ?", (entity_id,)).fetchone()
        if not row:
            raise ValueError(f"Entity '{entity_name}' with ID '{entity_id}' not found.")

        result = dict(row)

        # Look up child related records
        child_relations = [r for r in spec.relationships if r.source_entity == ent.name]
        related_data: dict[str, list[dict[str, Any]]] = {}
        for cr in child_relations:
            child_rows = conn.execute(
                f"SELECT * FROM {cr.target_entity} WHERE {cr.foreign_key_name} = ? LIMIT 50",
                (entity_id,),
            ).fetchall()
            related_data[cr.target_entity] = [dict(r) for r in child_rows]

        result["_related"] = related_data
        return result


def create_entity(
    db_path: Path | str,
    entity_name: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    """Create a new record for an entity."""
    with _connect(db_path) as conn:
        spec = _load_app_spec(conn)
        ent = next((e for e in spec.entities if e.name.lower() == entity_name.lower()), None)
        if not ent:
            raise ValueError(f"Unknown entity '{entity_name}'.")

        if ent.primary_key not in fields:
            max_row = conn.execute(f"SELECT COUNT(*) FROM {ent.name}").fetchone()[0]
            fields[ent.primary_key] = f"{ent.name[:3].upper()}-{max_row + 1:04d}"

        cols = list(fields.keys())
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO {ent.name} ({', '.join(cols)}) VALUES ({placeholders})"
        conn.execute(sql, tuple(fields[c] for c in cols))
        conn.commit()
        return {"created": True, "entity_name": ent.name, "id": fields[ent.primary_key], "fields": fields}


def update_entity(
    db_path: Path | str,
    entity_name: str,
    entity_id: str,
    fields: dict[str, Any],
) -> dict[str, Any]:
    """Update fields on an existing entity record."""
    with _connect(db_path) as conn:
        spec = _load_app_spec(conn)
        ent = next((e for e in spec.entities if e.name.lower() == entity_name.lower()), None)
        if not ent:
            raise ValueError(f"Unknown entity '{entity_name}'.")

        update_cols = []
        params = []
        for k, v in fields.items():
            if k != ent.primary_key:
                update_cols.append(f"{k} = ?")
                params.append(v)

        if not update_cols:
            return {"updated": False, "message": "No fields to update"}

        params.append(entity_id)
        sql = f"UPDATE {ent.name} SET {', '.join(update_cols)} WHERE {ent.primary_key} = ?"
        conn.execute(sql, tuple(params))
        conn.commit()
        return {"updated": True, "entity_name": ent.name, "id": entity_id, "updated_fields": fields}


def transition_entity(
    db_path: Path | str,
    entity_name: str,
    entity_id: str,
    action: str,
    actor: str = "agent",
    actor_role: str = "admin",
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply a validated lifecycle transition to an entity."""
    with _connect(db_path) as conn:
        spec = _load_app_spec(conn)
        engine = StateMachineEngine(spec)
        res = engine.execute_transition(
            conn=conn,
            entity_name=entity_name,
            entity_id=entity_id,
            action_name=action,
            actor=actor,
            actor_role=actor_role,
            fields=fields,
        )
        conn.commit()
        return res


def get_audit_log(db_path: Path | str) -> list[dict[str, Any]]:
    """Retrieve append-only action audit trail."""
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM action_logs ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]


def export_state(db_path: Path | str) -> dict[str, Any]:
    """Export complete relational database state."""
    with _connect(db_path) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name ASC")
        tables = [r[0] for r in cursor.fetchall()]
        res: dict[str, list[dict[str, Any]]] = {}
        for tbl in tables:
            rows = conn.execute(f"SELECT * FROM {tbl} ORDER BY 1 ASC").fetchall()
            res[tbl] = [dict(r) for r in rows]
        return res


def calculate_state_hash(db_path: Path | str) -> str:
    """Calculate reproducible SHA-256 state hash."""
    return calculate_database_hash(db_path)


class SoftwareService:
    """Object-oriented interface to the Software Environment service layer."""

    def __init__(self, db_path: Path | str, spec: AppSpec | None = None) -> None:
        self.db_path = Path(db_path)
        self._spec = spec

    def get_schema(self) -> dict[str, Any]:
        return get_schema(self.db_path)

    def search_entities(
        self,
        entity_name: str,
        query: str | None = None,
        status_filter: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        filters = {"status": status_filter} if status_filter else None
        res = search_entities(self.db_path, entity_name, query=query or "", filters=filters, page=1, page_size=limit)
        return res.get("items", [])

    def get_entity(self, entity_name: str, entity_id: str) -> dict[str, Any] | None:
        try:
            return get_entity(self.db_path, entity_name, entity_id)
        except Exception:
            return None

    def create_entity(
        self,
        entity_name: str,
        fields: dict[str, Any],
        actor: str = "agent",
    ) -> dict[str, Any]:
        return create_entity(self.db_path, entity_name, fields)

    def update_entity(
        self,
        entity_name: str,
        entity_id: str,
        fields: dict[str, Any],
        actor: str = "agent",
    ) -> dict[str, Any]:
        return update_entity(self.db_path, entity_name, entity_id, fields)

    def transition_entity(
        self,
        entity_name: str,
        entity_id: str,
        action: str,
        actor: str = "agent",
        actor_role: str = "admin",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            res = transition_entity(self.db_path, entity_name, entity_id, action, actor=actor, actor_role=actor_role, fields=payload)
            return {
                "success": True,
                "new_status": res.get("to_state"),
                "transition": res,
            }
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    def get_audit_log(
        self,
        entity_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        logs = get_audit_log(self.db_path)
        if entity_id:
            logs = [l for l in logs if l.get("entity_id") == entity_id]
        if limit:
            logs = logs[:limit]
        return logs

    def export_state(self) -> dict[str, Any]:
        return export_state(self.db_path)

    def calculate_state_hash(self) -> str:
        return calculate_state_hash(self.db_path)

    def submit_task(self, summary: str, affected_ids: str = "") -> dict[str, Any]:
        """Record formal task completion in the application audit log."""
        parsed_ids = [i.strip() for i in affected_ids.split(",") if i.strip()] if affected_ids else []
        with _connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO action_logs (
                    timestamp_iso, actor, entity_name, action, entity_id, from_state, to_state, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "2026-10-15T09:00:00Z",
                    "agent",
                    "Task",
                    "submit_task",
                    "task_completion",
                    "in_progress",
                    "completed",
                    json.dumps({"summary": summary, "affected_ids": parsed_ids}),
                ),
            )
            conn.commit()
        return {"submitted": True, "summary": summary, "affected_ids": parsed_ids, "status": "completed"}

