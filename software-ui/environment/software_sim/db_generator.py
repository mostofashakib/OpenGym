"""Dynamic relational database compiler and synthetic record generator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sqlite3
from typing import Any

from .spec import AppSpec, FieldType


def _field_type_to_sql(ft: FieldType) -> str:
    if ft in (FieldType.INTEGER, FieldType.BOOLEAN):
        return "INTEGER"
    elif ft == FieldType.FLOAT:
        return "REAL"
    else:
        return "TEXT"


def compile_schema(conn: sqlite3.Connection, spec: AppSpec) -> None:
    """Dynamically generate SQLite CREATE TABLE statements from AppSpec."""
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")

    # System & Audit tables
    conn.execute(
        """CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_iso TEXT NOT NULL,
            actor TEXT NOT NULL,
            entity_name TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            from_state TEXT NOT NULL DEFAULT '',
            to_state TEXT NOT NULL DEFAULT '',
            payload_json TEXT NOT NULL DEFAULT '{}'
        );"""
    )

    # Dynamic Entity tables
    for ent in spec.entities:
        col_defs: list[str] = [f"{ent.primary_key} TEXT PRIMARY KEY"]
        for f in ent.fields:
            if f.name == ent.primary_key:
                continue
            sql_type = _field_type_to_sql(f.field_type)
            req = " NOT NULL" if f.required and f.default is not None else ""
            col_defs.append(f"{f.name} {sql_type}{req}")

        # Add foreign keys
        for rel in spec.relationships:
            if rel.source_entity == ent.name:
                pass  # source has many targets
            elif rel.target_entity == ent.name:
                col_defs.append(f"FOREIGN KEY({rel.foreign_key_name}) REFERENCES {rel.source_entity}(id)")

        tbl_sql = f"CREATE TABLE IF NOT EXISTS {ent.name} (\n  " + ",\n  ".join(col_defs) + "\n);"
        conn.execute(tbl_sql)


def populate_synthetic_database(
    conn: sqlite3.Connection,
    spec: AppSpec,
    total_records: int = 600,
) -> dict[str, int]:
    """Populate dynamic entity tables with deterministic synthetic data and edge cases."""
    rng = random.Random(spec.seed)
    counts: dict[str, int] = {}

    # Store spec in system_state
    conn.execute(
        "INSERT INTO system_state (key, value) VALUES (?, ?)",
        ("spec_json", json.dumps(spec.as_dict())),
    )
    conn.execute(
        "INSERT INTO system_state (key, value) VALUES (?, ?)",
        ("seed", str(spec.seed)),
    )
    conn.execute(
        "INSERT INTO system_state (key, value) VALUES (?, ?)",
        ("domain", spec.domain),
    )
    conn.execute(
        "INSERT INTO system_state (key, value) VALUES (?, ?)",
        ("virtual_time_iso", "2026-10-14T09:00:00Z"),
    )

    cities = ["New York", "Chicago", "Dallas", "Atlanta", "Seattle", "Los Angeles", "Denver", "Miami"]
    names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Pat", "Riley", "Casey", "Jamie"]

    generated_ids: dict[str, list[str]] = {e.name: [] for e in spec.entities}

    # Pass 1: Generate parent / primary entities first
    for ent in spec.entities:
        is_child = any(r.target_entity == ent.name for r in spec.relationships)
        num_to_gen = int(total_records * 0.4) if not is_child else int(total_records * 0.6)
        num_to_gen = max(10, min(num_to_gen, 400))

        rows_inserted = 0
        for i in range(1, num_to_gen + 1):
            record_id = f"{ent.name[:3].upper()}-{i:04d}"
            generated_ids[ent.name].append(record_id)

            row_data: dict[str, Any] = {ent.primary_key: record_id}

            for f in ent.fields:
                if f.name == ent.primary_key:
                    continue

                if f.field_type == FieldType.FOREIGN_KEY and f.foreign_entity:
                    available = generated_ids.get(f.foreign_entity, [])
                    row_data[f.name] = rng.choice(available) if available else None
                elif f.field_type == FieldType.ENUM and f.enum_values:
                    row_data[f.name] = rng.choice(f.enum_values)
                elif f.field_type == FieldType.INTEGER:
                    if "delay" in f.name:
                        # Edge cases: some delayed by 3-7 days, others 0
                        row_data[f.name] = rng.choice([0, 0, 0, 1, 3, 5, 8])
                    else:
                        row_data[f.name] = rng.randint(1, 100)
                elif f.field_type == FieldType.FLOAT:
                    row_data[f.name] = round(rng.uniform(10.0, 500.0), 2)
                elif f.field_type == FieldType.BOOLEAN:
                    row_data[f.name] = 1 if rng.random() > 0.5 else 0
                else:
                    if "name" in f.name:
                        row_data[f.name] = f"{rng.choice(names)} {rng.choice(cities)}"
                    elif "code" in f.name or "tracking" in f.name:
                        row_data[f.name] = f"{f.name[:3].upper()}-{rng.randint(10000, 99999)}"
                    elif "city" in f.name or "origin" in f.name or "destination" in f.name:
                        row_data[f.name] = rng.choice(cities)
                    else:
                        row_data[f.name] = f"Synthetic {f.name} for {record_id}"

            # Ingest intentional edge cases: occasional null in optional fields
            if rng.random() < 0.05:
                for k in list(row_data.keys()):
                    if k != ent.primary_key and rng.random() < 0.2:
                        f_spec = next((f for f in ent.fields if f.name == k), None)
                        if f_spec and not (f_spec.required and f_spec.default is not None):
                            row_data[k] = None

            cols = list(row_data.keys())
            placeholders = ", ".join(["?"] * len(cols))
            sql = f"INSERT INTO {ent.name} ({', '.join(cols)}) VALUES ({placeholders})"
            conn.execute(sql, tuple(row_data[c] for c in cols))
            rows_inserted += 1

        counts[ent.name] = rows_inserted

    return counts


def create_dynamic_database(
    db_path: Path | str,
    spec: AppSpec,
) -> dict[str, Any]:
    """Create complete database for the given AppSpec."""
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    try:
        compile_schema(conn, spec)
        counts = populate_synthetic_database(conn, spec)
        conn.commit()
    finally:
        conn.close()

    return {"spec_name": spec.name, "domain": spec.domain, "counts": counts}


def calculate_database_hash(db_path: Path | str) -> str:
    """Compute deterministic SHA-256 hash over all entity tables."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name ASC")
        tables = [r[0] for r in cursor.fetchall() if r[0] not in ("action_logs",)]
        data: dict[str, list[dict[str, Any]]] = {}
        for tbl in tables:
            rows = conn.execute(f"SELECT * FROM {tbl} ORDER BY 1 ASC").fetchall()
            data[tbl] = [dict(r) for r in rows]
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    finally:
        conn.close()


class DatabaseGenerator:
    """Convenience class for generating and seeding databases from an AppSpec."""

    def __init__(self, spec: AppSpec, seed: int = 42) -> None:
        if spec.seed != seed:
            spec = AppSpec(
                name=spec.name,
                domain=spec.domain,
                description=spec.description,
                seed=seed,
                entities=spec.entities,
                workflows=spec.workflows,
                relationships=spec.relationships,
                roles=spec.roles,
                layout=spec.layout,
            )
        self.spec = spec
        self.seed = seed

    def populate_database(self, db_path: Path | str, records_per_entity: int = 25) -> str:
        create_dynamic_database(db_path, self.spec)
        return calculate_database_hash(db_path)

