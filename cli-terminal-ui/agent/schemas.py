"""Output schemas, generated from the tool definitions.

Every model call carries a schema, so what comes back is constrained at decode
time rather than parsed hopefully. What that schema *is* differs by service:

* Ollama constrains the whole message with ``format``, and ``format`` and
  ``tools`` are mutually exclusive -- send both and tool calls silently stop
  coming back. So the tool surface is expressed *as* the schema: one action
  object whose ``tool`` is an enum over the real tool names and whose
  ``arguments`` are that tool's own input schema, selected by a discriminated
  union.
* Standard schema-constrained endpoints constrain function arguments with ``strict: true``
  on the function definition, which is the same guarantee reached the other way
  round -- but strict mode has its own rules about what a schema may look like,
  so ours are normalized to meet them.
* Anthropic validates ``input_schema`` server-side and returns arguments already
  decoded.

A schema pins the shape and says nothing about meaning, so :func:`render_catalogue`
puts the names, arguments and descriptions in the prompt.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

THOUGHT_KEY = "thought"
ACTIONS_KEY = "actions"
ANSWER_KEY = "answer"


def normalize_tool_entry(tool: Any) -> dict[str, Any]:
    """Ensure a tool entry is a dictionary with at least name, description, and input_schema."""
    if isinstance(tool, Mapping):
        schema = tool.get("input_schema")
        return {
            "name": str(tool.get("name", "")),
            "description": str(tool.get("description", "")),
            "input_schema": dict(schema) if isinstance(schema, Mapping) else {"type": "object", "properties": {}},
        }
    if isinstance(tool, str):
        return {
            "name": tool,
            "description": f"Tool {tool}",
            "input_schema": {"type": "object", "properties": {}},
        }
    return {
        "name": str(tool),
        "description": "",
        "input_schema": {"type": "object", "properties": {}},
    }


def build_action_schema(tools: Sequence[Any]) -> dict[str, Any]:
    """One turn of output, as a JSON schema.

    ``actions`` is an array so a model can act more than once in a turn, and
    empty so it can stop: no actions plus an ``answer`` is how an episode ends.
    """
    normalized_tools = [normalize_tool_entry(tool) for tool in tools]
    variants = [
        {
            "type": "object",
            "properties": {
                "tool": {"const": tool["name"]},
                "arguments": _as_object_schema(tool.get("input_schema")),
            },
            "required": ["tool", "arguments"],
            "additionalProperties": False,
        }
        for tool in normalized_tools
    ]
    if not variants:
        variants = [{"type": "object", "properties": {}, "additionalProperties": False}]

    return {
        "type": "object",
        "properties": {
            THOUGHT_KEY: {
                "type": "string",
                "description": "Brief reasoning about what step to take next.",
            },
            ACTIONS_KEY: {
                "type": "array",
                "items": {"anyOf": variants} if len(variants) > 1 else variants[0],
                "description": (
                    "Tools to call on this turn. Empty when you have completed the task."
                ),
            },
            ANSWER_KEY: {
                "type": "string",
                "description": "Final message or summary once finished.",
            },
        },
        "required": [THOUGHT_KEY, ACTIONS_KEY, ANSWER_KEY],
        "additionalProperties": False,
    }


def strict_parameters(schema: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize a tool's `input_schema` so standard strict-mode validators accept it.

    Rules for strict mode schemas:
    1. `additionalProperties` must be explicitly False on every object.
    2. Every declared property must be named in `required`.
    3. Null values must be explicit unions (`type: [..., "null"]`).
    """
    if not schema:
        return {"type": "object", "properties": {}, "required": [], "additionalProperties": False}
    return _strict_node(dict(schema))


def _strict_node(node: Any) -> Any:
    if not isinstance(node, dict):
        return node
    out = dict(node)
    node_type = out.get("type")
    if node_type == "object" or "properties" in out:
        out["type"] = "object"
        properties = {
            key: _strict_node(val) for key, val in (out.get("properties") or {}).items()
        }
        out["properties"] = properties
        out["required"] = sorted(properties.keys())
        out["additionalProperties"] = False
    elif node_type == "array" and "items" in out:
        out["items"] = _strict_node(out["items"])
    return out


def _as_object_schema(schema: Any) -> dict[str, Any]:
    if isinstance(schema, Mapping):
        return dict(schema)
    return {"type": "object", "properties": {}, "additionalProperties": False}


def render_catalogue(tools: Sequence[Any]) -> str:
    """A human-readable markdown block of the available tools."""
    lines = ["Available tools:"]
    for raw_tool in tools:
        tool = normalize_tool_entry(raw_tool)
        lines.append(f"\n### `{tool['name']}`")
        if tool.get("description"):
            lines.append(tool["description"].strip())
        schema = tool.get("input_schema") or {}
        props = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        if props and isinstance(props, Mapping):
            lines.append("Arguments:")
            for name, spec in props.items():
                req_marker = " (required)" if name in required else " (optional)"
                spec_dict = spec if isinstance(spec, Mapping) else {}
                prop_type = spec_dict.get("type", "any")
                prop_desc = f" - {spec_dict['description']}" if "description" in spec_dict else ""
                lines.append(f"- `{name}` [{prop_type}]{req_marker}{prop_desc}")
    return "\n".join(lines)


def drop_nulls(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: drop_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [drop_nulls(v) for v in value if v is not None]
    return value
