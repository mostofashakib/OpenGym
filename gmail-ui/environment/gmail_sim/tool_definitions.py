"""Model-facing JSON-schema definitions for the Gmail world actions."""

from __future__ import annotations

from typing import Any


def _tool(
    name: str,
    description: str,
    properties: dict[str, dict[str, Any]],
    required: list[str],
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


TEXT = {"type": "string"}
BOOLEAN = {"type": "boolean"}
STRING_LIST = {"type": "array", "items": {"type": "string"}}
ADDRESSES = {
    "anyOf": [
        {"type": "string"},
        {"type": "array", "items": {"type": "string"}},
    ]
}

TOOL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    _tool(
        "list_emails",
        "List email messages matching optional filters such as folder (inbox, sent, archive, trash, starred, important), unread, starred, important, search query q, or label.",
        {
            "folder": TEXT,
            "starred": BOOLEAN,
            "important": BOOLEAN,
            "unread": BOOLEAN,
            "q": TEXT,
            "query": TEXT,
            "label": TEXT,
        },
        [],
    ),
    _tool(
        "get_email",
        "Retrieve the full details of a single email message by its ID.",
        {"id": TEXT, "email_id": TEXT},
        ["id"],
    ),
    _tool(
        "send_email",
        "Send a new email message to one or more recipient addresses.",
        {
            "to": ADDRESSES,
            "cc": STRING_LIST,
            "bcc": STRING_LIST,
            "subject": TEXT,
            "body": TEXT,
            "text": TEXT,
            "parent_thread_id": TEXT,
        },
        ["to", "body"],
    ),
    _tool(
        "update_email",
        "Update message state such as read/unread, starred, important, archive, trash, or modify labels.",
        {
            "id": TEXT,
            "email_id": TEXT,
            "isRead": BOOLEAN,
            "is_read": BOOLEAN,
            "isStarred": BOOLEAN,
            "is_starred": BOOLEAN,
            "isImportant": BOOLEAN,
            "is_important": BOOLEAN,
            "isArchived": BOOLEAN,
            "is_archived": BOOLEAN,
            "isTrash": BOOLEAN,
            "is_trash": BOOLEAN,
            "action": TEXT,
            "addLabels": STRING_LIST,
            "add_labels": STRING_LIST,
            "removeLabels": STRING_LIST,
            "remove_labels": STRING_LIST,
        },
        ["id"],
    ),
    _tool(
        "list_threads",
        "List email conversation threads ordered by last activity date.",
        {"folder": TEXT, "q": TEXT, "query": TEXT},
        [],
    ),
    _tool(
        "get_thread",
        "Retrieve a thread and all messages within it by thread ID.",
        {"id": TEXT, "thread_id": TEXT},
        ["id"],
    ),
    _tool(
        "reply_thread",
        "Reply to an existing conversation thread.",
        {
            "thread_id": TEXT,
            "id": TEXT,
            "body": TEXT,
            "text": TEXT,
            "to": STRING_LIST,
        },
        ["thread_id", "body"],
    ),
    _tool(
        "list_drafts",
        "List all saved email drafts.",
        {},
        [],
    ),
    _tool(
        "create_draft",
        "Create and save a new draft email without sending it.",
        {
            "to": ADDRESSES,
            "cc": STRING_LIST,
            "bcc": STRING_LIST,
            "subject": TEXT,
            "body": TEXT,
            "text": TEXT,
        },
        [],
    ),
    _tool(
        "update_draft",
        "Update the recipients, subject, or content of an existing draft.",
        {
            "id": TEXT,
            "draft_id": TEXT,
            "to": ADDRESSES,
            "subject": TEXT,
            "body": TEXT,
            "text": TEXT,
        },
        ["id"],
    ),
    _tool(
        "send_draft",
        "Send an existing draft email by its ID and remove it from drafts.",
        {"id": TEXT, "draft_id": TEXT},
        ["id"],
    ),
    _tool(
        "delete_draft",
        "Permanently delete an email draft by its ID.",
        {"id": TEXT, "draft_id": TEXT},
        ["id"],
    ),
    _tool(
        "list_labels",
        "List all system and user-defined email labels.",
        {},
        [],
    ),
    _tool(
        "create_label",
        "Create a new user label with a specified name and optional color hex code.",
        {"name": TEXT, "color": TEXT},
        ["name"],
    ),
    _tool(
        "search_emails",
        "Search email messages by query text matching subject, body, or sender.",
        {"query": TEXT, "q": TEXT},
        ["query"],
    ),
    _tool(
        "list_contacts",
        "List known address book contacts.",
        {},
        [],
    ),
    _tool(
        "get_counters",
        "Get counts of unread inbox messages, total inbox, starred messages, and drafts.",
        {},
        [],
    ),
    _tool(
        "submit_task",
        "Submit final task completion summary and list of affected message IDs.",
        {
            "summary": TEXT,
            "affected_message_ids": STRING_LIST,
            "affectedMessageIds": STRING_LIST,
        },
        [],
    ),
)


def get_tool_definitions() -> tuple[dict[str, Any], ...]:
    return TOOL_DEFINITIONS
