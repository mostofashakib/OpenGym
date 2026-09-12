"""Tool schemas and validation for the terminal environment."""

from __future__ import annotations

from typing import Any

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "run_command",
        "description": "Execute a shell command inside the virtual Linux terminal environment (e.g. ps, kill, df, ls, cat, grep, find, chmod, systemctl, head, tail, etc.).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command line string to execute.",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory for the command execution (default: /home/admin).",
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
    {
        "name": "read_file",
        "description": "Read file contents from the virtual filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file.",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line offset (0-indexed) to start reading from.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to return.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "write_file",
        "description": "Write or append text content to a file in the virtual filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the target file.",
                },
                "content": {
                    "type": "string",
                    "description": "The text content to write.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "description": "Write mode: 'write' (overwrite) or 'append'. Default is 'write'.",
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_processes",
        "description": "Enumerate running processes, resource utilization (CPU, memory), and statuses.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Optional filter for process status (e.g. 'running', 'terminated').",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "inspect_system",
        "description": "Retrieve host health summary, disk filesystem usage, total memory, and active services.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "submit_task",
        "description": "Submit final incident response remediation report and conclusion.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Summary of incident investigation, root cause diagnosis, and remediation actions.",
                },
                "actions_taken": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific remediation actions performed.",
                },
            },
            "required": ["summary", "actions_taken"],
            "additionalProperties": False,
        },
    },
]


def get_tool_definitions() -> list[dict[str, Any]]:
    return [dict(t) for t in TOOL_DEFINITIONS]
