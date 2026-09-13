"""FastMCP Server exposing the Generative Software Environment tools over stdio.

Enables agents to interact with procedurally generated business applications
regardless of domain schema, UI layout, or terminology.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .context import SoftwareContext

# Initialize FastMCP Server
mcp = FastMCP("software-environment")

# Initialize global context
_DB_PATH = os.environ.get("SOFTWARE_DB_PATH", "/tmp/software_sim.db")
_APP_SPEC_PATH = os.environ.get("SOFTWARE_SPEC_PATH", "")

_context = SoftwareContext(
    db_path=_DB_PATH,
    app_spec_path=_APP_SPEC_PATH if os.path.exists(_APP_SPEC_PATH) else None,
)


@mcp.tool()
def get_application_schema() -> str:
    """Retrieve the declarative schema of the current software application.

    Returns the entities, field types, valid lifecycle states, allowed workflow transitions,
    and visual layout information. Use this to understand the application structure.
    """
    schema = _context.service.get_schema()
    return json.dumps(schema, indent=2)


@mcp.tool()
def search_entities(
    entity_name: str,
    query: str = "",
    status_filter: str = "",
    limit: int = 50,
) -> str:
    """Search and filter records for a specific entity type.

    Args:
        entity_name: The name/type of entity to search (e.g. 'Shipment', 'Device', 'Student').
        query: Optional free-text search across primary text fields.
        status_filter: Optional filter by workflow status/state.
        limit: Maximum number of records to return (default 50).
    """
    records = _context.service.search_entities(
        entity_name=entity_name,
        query=query if query else None,
        status_filter=status_filter if status_filter else None,
        limit=limit,
    )
    return json.dumps(records, indent=2)


@mcp.tool()
def get_entity_details(entity_name: str, entity_id: str) -> str:
    """Retrieve full details of a specific entity record, including field values and valid next actions.

    Args:
        entity_name: The name/type of entity.
        entity_id: The unique identifier of the entity record.
    """
    record = _context.service.get_entity(entity_name=entity_name, entity_id=entity_id)
    if record is None:
        return json.dumps({"error": f"Record {entity_id} not found in {entity_name}."})
    return json.dumps(record, indent=2)


@mcp.tool()
def create_entity(
    entity_name: str,
    fields_json: str,
    actor: str = "agent",
) -> str:
    """Create a new entity record in the application.

    Args:
        entity_name: The entity type to create.
        fields_json: JSON string of field name to value mappings.
        actor: The role or user creating the record (default: 'agent').
    """
    try:
        fields = json.loads(fields_json)
        if not isinstance(fields, dict):
            return json.dumps({"error": "fields_json must encode a dictionary."})
    except Exception as exc:
        return json.dumps({"error": f"Invalid JSON format: {exc}"})

    result = _context.service.create_entity(entity_name=entity_name, fields=fields, actor=actor)
    return json.dumps(result, indent=2)


@mcp.tool()
def update_entity_fields(
    entity_name: str,
    entity_id: str,
    fields_json: str,
    actor: str = "agent",
) -> str:
    """Update editable fields on an existing entity record.

    Args:
        entity_name: The entity type.
        entity_id: The ID of the record to update.
        fields_json: JSON string of field updates.
        actor: The actor executing the update.
    """
    try:
        fields = json.loads(fields_json)
        if not isinstance(fields, dict):
            return json.dumps({"error": "fields_json must encode a dictionary."})
    except Exception as exc:
        return json.dumps({"error": f"Invalid JSON format: {exc}"})

    result = _context.service.update_entity(
        entity_name=entity_name,
        entity_id=entity_id,
        fields=fields,
        actor=actor,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def transition_entity_workflow(
    entity_name: str,
    entity_id: str,
    action: str,
    actor: str = "agent",
    actor_role: str = "admin",
    reason: str = "",
) -> str:
    """Execute a lifecycle state transition on an entity according to workflow rules.

    Args:
        entity_name: The entity type.
        entity_id: The ID of the record.
        action: The workflow action trigger (e.g. 'approve', 'dispatch', 'resolve', 'archive').
        actor: Name/ID of the actor executing the action.
        actor_role: The role assumed for permission checking (default: 'admin').
        reason: Optional justification or comment for the transition.
    """
    payload = {"reason": reason} if reason else None
    result = _context.service.transition_entity(
        entity_name=entity_name,
        entity_id=entity_id,
        action=action,
        actor=actor,
        actor_role=actor_role,
        payload=payload,
    )
    return json.dumps(result, indent=2)


@mcp.tool()
def get_audit_trail(entity_id: str = "", limit: int = 50) -> str:
    """Query the system audit log of executed actions and state transitions.

    Args:
        entity_id: Optional filter for actions on a specific entity ID.
        limit: Max entries to return.
    """
    logs = _context.service.get_audit_log(entity_id=entity_id if entity_id else None, limit=limit)
    return json.dumps(logs, indent=2)


@mcp.tool()
def submit_task(summary: str, affected_entity_ids: str = "") -> str:
    """Submit completion of the software application task.

    Args:
        summary: Clear summary of the state transitions and operations executed.
        affected_entity_ids: Optional comma-separated list of affected record IDs.
    """
    return json.dumps({
        "submitted": True,
        "summary": summary,
        "affected_ids": [i.strip() for i in affected_entity_ids.split(",") if i.strip()],
        "status": "completed",
    }, indent=2)


def main() -> None:
    """Entry point for the MCP stdio server."""
    mcp.run()


if __name__ == "__main__":
    main()
