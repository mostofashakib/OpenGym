"""Tool schemas for the headless browser environment."""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "navigate",
        "description": "Navigate the browser to a specific internal portal URL (e.g. 'https://procure.corp/dashboard', '/orders', '/vendors', '/compliance', '/orders/PO-9821').",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The destination URL or portal path.",
                },
            },
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_page",
        "description": "Inspect the currently active web page: returns title, structured text/DOM content, and list of interactive element IDs.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "click",
        "description": "Click an interactive button, link, or tab identified by its element ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {
                    "type": "string",
                    "description": "The unique ID of the element to click (e.g. 'btn-approve-po-3410', 'btn-reject-po-9821', 'tab-vendors').",
                },
            },
            "required": ["element_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "type_text",
        "description": "Type text into an input field or textarea identified by its element ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {
                    "type": "string",
                    "description": "The unique ID of the input field.",
                },
                "text": {
                    "type": "string",
                    "description": "The text string to enter.",
                },
            },
            "required": ["element_id", "text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "select_option",
        "description": "Select an option from a dropdown / select element.",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {
                    "type": "string",
                    "description": "The unique ID of the select element.",
                },
                "value": {
                    "type": "string",
                    "description": "The value or option text to select.",
                },
            },
            "required": ["element_id", "value"],
            "additionalProperties": False,
        },
    },
    {
        "name": "submit_form",
        "description": "Submit a form identified by its form ID (or active form).",
        "parameters": {
            "type": "object",
            "properties": {
                "form_id": {
                    "type": "string",
                    "description": "The unique ID of the form to submit.",
                },
            },
            "required": ["form_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "go_back",
        "description": "Navigate back to the previous page in browser history.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "submit_task",
        "description": "Submit final procurement audit conclusion and report.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Summary of audited purchase orders, suspended vendors, and compliance recertifications.",
                },
                "audited_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of affected purchase order and vendor IDs.",
                },
            },
            "required": ["summary", "audited_ids"],
            "additionalProperties": False,
        },
    },
]


def get_tool_definitions() -> list[dict[str, Any]]:
    return [dict(t) for t in TOOL_DEFINITIONS]
