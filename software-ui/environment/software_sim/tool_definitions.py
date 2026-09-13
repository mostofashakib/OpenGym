"""Tool definitions for FastMCP and agent harnesses interacting with generated software apps."""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_schema",
        "description": "Discover the generated application's data model, entities, field types, workflows, and layout navigation.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "search_entities",
        "description": "Search, filter, and paginate records of a specified entity type.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Name of the entity (e.g. Shipment, Student, WorkOrder)"},
                "query": {"type": "string", "default": "", "description": "Text search query"},
                "filters": {"type": "object", "description": "Key-value filter dictionary"},
                "sort_by": {"type": "string", "description": "Column name to sort by"},
                "page": {"type": "integer", "default": 1, "description": "Page number"},
                "page_size": {"type": "integer", "default": 25, "description": "Results per page"},
            },
            "required": ["entity_name"],
        },
    },
    {
        "name": "get_entity",
        "description": "Retrieve full details and related child records for a specific entity ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity name"},
                "entity_id": {"type": "string", "description": "Primary key ID of the record"},
            },
            "required": ["entity_name", "entity_id"],
        },
    },
    {
        "name": "create_entity",
        "description": "Create a new record in the application database.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity name"},
                "fields": {"type": "object", "description": "Field key-values for the new record"},
            },
            "required": ["entity_name", "fields"],
        },
    },
    {
        "name": "update_entity",
        "description": "Update fields on an existing entity record.",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity name"},
                "entity_id": {"type": "string", "description": "Record ID to update"},
                "fields": {"type": "object", "description": "Field key-values to modify"},
            },
            "required": ["entity_name", "entity_id", "fields"],
        },
    },
    {
        "name": "transition_entity",
        "description": "Execute an authoritative state machine transition on an entity (e.g. dispatch, approve, clear).",
        "parameters": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Entity name"},
                "entity_id": {"type": "string", "description": "Record ID"},
                "action": {"type": "string", "description": "Workflow transition action name"},
                "fields": {"type": "object", "description": "Optional accompanying field updates"},
            },
            "required": ["entity_name", "entity_id", "action"],
        },
    },
    {
        "name": "get_audit_log",
        "description": "Retrieve the append-only log of actions and state transitions performed in the application.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]
