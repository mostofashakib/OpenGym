"""Declarative schema and workflow specification importer for custom enterprise environments."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional


class EnterpriseSchemaImporter:
    """Imports declarative organization definitions, role hierarchies, and policy specifications."""

    @staticmethod
    def import_from_json(conn: sqlite3.Connection, spec_path: Path | str) -> Dict[str, Any]:
        """Import roles, departments, policy rules, and workflow specs from a declarative JSON bundle."""
        with open(spec_path, "r", encoding="utf-8") as f:
            spec: Dict[str, Any] = json.load(f)

        imported = {
            "departments": 0,
            "roles": 0,
            "policies": 0,
        }

        # 1. Departments
        for dept in spec.get("departments", []):
            conn.execute(
                "INSERT OR REPLACE INTO departments (id, name, code, lead_id) VALUES (?, ?, ?, ?)",
                (dept["id"], dept["name"], dept["code"], dept.get("lead_id", "")),
            )
            imported["departments"] += 1

        # 2. Roles
        for role in spec.get("roles", []):
            conn.execute(
                """INSERT OR REPLACE INTO roles (id, title, department, approval_limit_usd, permissions_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    role["id"],
                    role["title"],
                    role["department"],
                    role.get("approval_limit_usd", 0.0),
                    json.dumps(role.get("permissions", [])),
                ),
            )
            imported["roles"] += 1

        # 3. Policy Rules
        for pol in spec.get("policies", []):
            conn.execute(
                """INSERT OR REPLACE INTO policy_rules (id, name, category, description, rule_config_json, severity, is_active)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    pol["id"],
                    pol["name"],
                    pol["category"],
                    pol["description"],
                    json.dumps(pol.get("rule_config", {})),
                    pol.get("severity", "critical"),
                    1 if pol.get("is_active", True) else 0,
                ),
            )
            imported["policies"] += 1

        conn.commit()
        return {"success": True, "imported_counts": imported}
