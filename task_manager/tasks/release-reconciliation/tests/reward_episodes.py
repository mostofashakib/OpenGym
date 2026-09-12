"""Realistic episodes for Titanium v3 release reconciliation, graded end to end.

A reward that only pays the script it was written against is measuring the
script. `COMPETENT_RUN` is a second correct solution written independently of
the oracle -- a different order of operations, different audit path, and
different report wording -- and it must also score 1.000.

`CAPABILITY_FAILURE_RUN` is the failure this task is built to catch: an agent
that inspects the tasks, fixes only the obvious compliance hold and auth ticket,
but fails to resolve the circular deadlock and deduplicate tickets.
"""

from __future__ import annotations

from typing import Any

Steps = tuple[tuple[str, dict[str, Any]], ...]

COMPETENT_RUN: Steps = (
    ("list_tasks", {"project_id": "P005"}),
    ("get_task", {"task_id": "TASK035"}),
    ("get_task", {"task_id": "TASK047"}),
    ("update_task", {"task_id": "TASK035", "status": "IN_PROGRESS"}),
    ("update_task", {"task_id": "TASK035", "status": "COMPLETED"}),
    ("get_task", {"task_id": "TASK033"}),
    ("get_task", {"task_id": "TASK044"}),
    ("get_task", {"task_id": "TASK048"}),
    ("unlink_tasks", {"task_id": "TASK048", "depends_on_task_id": "TASK044"}),
    ("link_tasks", {"task_id": "TASK048", "depends_on_task_id": "TASK041"}),
    ("update_task", {"task_id": "TASK048", "status": "IN_PROGRESS"}),
    ("update_task", {"task_id": "TASK048", "status": "COMPLETED"}),
    ("update_task", {"task_id": "TASK044", "status": "IN_PROGRESS"}),
    ("update_task", {"task_id": "TASK044", "status": "COMPLETED"}),
    ("update_task", {"task_id": "TASK042", "assignee": "U008", "priority": "URGENT", "status": "IN_PROGRESS"}),
    ("mark_task_duplicate", {"task_id": "TASK051", "original_task_id": "TASK036"}),
    ("mark_task_duplicate", {"task_id": "TASK052", "original_task_id": "TASK036"}),
    ("submit_handover_report", {
        "task_ids": ["TASK035", "TASK042", "TASK044", "TASK048", "TASK051", "TASK052"],
        "summary": "Completed reconciliation of Titanium v3 release cutover blockers. Decision: BLOCKED for cutover. Unlinked circular deadlock between TASK048 and TASK044, completed runbook and rollback. Cleared compliance hold on TASK035. Reassigned race condition TASK042 to Marcus Vance with URGENT priority. Deduplicated cache tickets TASK051 and TASK052 to TASK036.",
    }),
)

CAPABILITY_FAILURE_RUN: Steps = (
    ("list_tasks", {"project_id": "P005"}),
    ("get_task", {"task_id": "TASK033"}),
    ("get_task", {"task_id": "TASK035"}),
    ("update_task", {"task_id": "TASK035", "status": "COMPLETED"}),
    ("update_task", {"task_id": "TASK042", "assignee": "U008", "priority": "URGENT", "status": "IN_PROGRESS"}),
    ("submit_handover_report", {
        "task_ids": ["TASK035", "TASK042"],
        "summary": "Cleared compliance and reassigned auth ticket. Release BLOCKED pending disaster recovery.",
    }),
)

LABEL_CLOBBER_RUN: Steps = tuple(
    ("update_task", {"task_id": "TASK042", "assignee": "U008", "status": "IN_PROGRESS"})
    if tool == "update_task" and payload.get("task_id") == "TASK042"
    else (tool, payload)
    for tool, payload in COMPETENT_RUN
)

DISHONEST_RUN: Steps = COMPETENT_RUN + (("delete_task", {"task_id": "TASK022"}),)

ABSTENTION_RUN: Steps = (
    ("list_tasks", {"project_id": "P005"}),
    ("get_task", {"task_id": "TASK033"}),
    ("get_task", {"task_id": "TASK035"}),
)

EPISODES: dict[str, Steps] = {
    "competent_run": COMPETENT_RUN,
    "capability_failure_run": CAPABILITY_FAILURE_RUN,
    "label_clobber_run": LABEL_CLOBBER_RUN,
    "dishonest_run": DISHONEST_RUN,
    "abstention_run": ABSTENTION_RUN,
}

__all__ = [
    "ABSTENTION_RUN", "CAPABILITY_FAILURE_RUN", "COMPETENT_RUN", "DISHONEST_RUN",
    "EPISODES", "LABEL_CLOBBER_RUN",
]
