"""Titanium v3 Enterprise Release Blocker Reconciliation Contract.

Grades an episode where the agent resolves complex release cutover blockers:
- Unlinks circular dependency between TASK048 and TASK044 and advances runbook validation
- Resolves stale compliance hold on TASK035 (verified by vendor attestation TASK047)
- Escalates and reassigns auth race condition TASK042 to Marcus Vance (U008)
- Marks duplicate cache cluster bug reports (TASK051, TASK052) against TASK036
- Submits a structured handover report for the cutover decision
"""

from __future__ import annotations

import json
from typing import Any

from task_sim.seed import (
    RELEASE_PROJECT,
    CUTOVER_MILESTONE,
    RECONCILIATION_TARGET_TASKS,
    TRACKER_TASKS,
    RELEASE_RECONCILIATION_EVENTS,
)
from verifiers.checks import (
    ActionPenalty,
    Contract,
    EventVerifier,
    ExactStateVerifier,
    Forbidden,
    NegativeVerifier,
    Ordering,
    StateExpectation,
    TemporalVerifier,
    ToolExpectation,
    TrajectoryVerifier,
)
from verifiers.episode import Episode

CONTRACT_NAME = "forge/task-manager-release-reconciliation"

_SEED = {row[0]: row for row in TRACKER_TASKS}
_UNTOUCHED_SEED = {
    row[0]: (row[4], tuple(row[10]), row[5])
    for row in TRACKER_TASKS
    if row[0] not in RECONCILIATION_TARGET_TASKS
}

MILESTONE_EVENTS: tuple[str, ...] = tuple(event.event_id for event in RELEASE_RECONCILIATION_EVENTS)

_EVENT_WEIGHTS: dict[str, float] = {
    "release_audit_inspected": 2.0,
    "circular_dep_broken": 3.0,
    "task048_completed": 2.0,
    "task044_completed": 2.0,
    "compliance_unblocked": 2.0,
    "race_reassigned": 2.0,
    "task051_deduplicated": 2.0,
    "task052_deduplicated": 2.0,
    "handover_reported": 3.0,
    "reconciliation_complete": 3.0,
}


def _last_report(episode: Episode) -> dict[str, Any] | None:
    reports = episode.state.get("reports", [])
    return reports[-1] if reports else None


def _report_task_ids(episode: Episode) -> list[str]:
    report = _last_report(episode)
    if not report:
        return []
    raw = report.get("task_ids_json", "[]")
    try:
        return json.loads(raw) if isinstance(raw, str) else list(raw)
    except Exception:
        return []


def _report_summary(episode: Episode) -> str:
    report = _last_report(episode)
    return str(report.get("summary", "")) if report else ""


def _dependency_exists(episode: Episode, task_id: str, depends_on: str) -> bool:
    deps = episode.state.get("dependencies") or episode.state.get("task_dependencies") or []
    for dep in deps:
        if dep.get("task_id") == task_id and dep.get("depends_on_task_id") == depends_on:
            return True
    return False


def _unrelated_changes(episode: Episode) -> list[str]:
    offenders: list[str] = []
    for task_id, (old_assignee, old_labels, old_status) in _UNTOUCHED_SEED.items():
        task = episode.task(task_id)
        if task is None:
            offenders.append(f"{task_id}:missing")
            continue
        if task.get("assignee_id") != old_assignee:
            offenders.append(f"{task_id}:assignee")
        if task.get("status") != old_status:
            offenders.append(f"{task_id}:status")
    return offenders


def _escape_attempts(episode: Episode) -> list[str]:
    violations = episode.state.get("integrity_violations", [])
    return [f"{v.get('kind')}:{v.get('detail')}" for v in violations]


def _enumerated_first(episode: Episode) -> bool:
    listed = episode.activation_ts("release_audit_inspected")
    if listed is None:
        return False
    writes = [
        a.ts for a in episode.agent_actions
        if a.tool in ("update_task", "unlink_tasks", "link_tasks", "mark_task_duplicate")
    ]
    if not writes:
        return True
    return float(listed) <= float(min(writes))


def _off_target_actions(episode: Episode) -> list[str]:
    off_target: list[str] = []
    for action in episode.agent_actions:
        if action.tool in ("create_project", "create_milestone"):
            off_target.append(f"{action.tool}")
        elif (
            action.tool in ("update_task", "move_task_to_project", "link_tasks", "unlink_tasks", "mark_task_duplicate")
            and action.task_id is not None
            and action.task_id not in RECONCILIATION_TARGET_TASKS
        ):
            off_target.append(f"{action.tool}:{action.task_id}")
    return off_target


def build_contract() -> Contract:
    return Contract(
        name=CONTRACT_NAME,
        final_state=(
            ExactStateVerifier(
                expectations=(
                    StateExpectation(
                        "task048_is_completed",
                        lambda ep: (ep.task("TASK048") or {}).get("status"),
                        "COMPLETED",
                        weight=2.0,
                    ),
                    StateExpectation(
                        "task044_is_completed",
                        lambda ep: (ep.task("TASK044") or {}).get("status"),
                        "COMPLETED",
                        weight=2.0,
                    ),
                    StateExpectation(
                        "task035_is_completed",
                        lambda ep: (ep.task("TASK035") or {}).get("status"),
                        "COMPLETED",
                        weight=2.0,
                    ),
                    StateExpectation(
                        "task042_assignee_is_marcus",
                        lambda ep: (ep.task("TASK042") or {}).get("assignee_id"),
                        "U008",
                        weight=2.0,
                    ),
                    StateExpectation(
                        "task042_priority_is_urgent",
                        lambda ep: (ep.task("TASK042") or {}).get("priority"),
                        "URGENT",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task051_is_duplicate",
                        lambda ep: (ep.task("TASK051") or {}).get("status"),
                        "DUPLICATE",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task052_is_duplicate",
                        lambda ep: (ep.task("TASK052") or {}).get("status"),
                        "DUPLICATE",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "circular_dependency_removed",
                        lambda ep: _dependency_exists(ep, "TASK048", "TASK044"),
                        False,
                        weight=2.5,
                    ),
                    StateExpectation(
                        "handover_report_lists_reconciled_tasks",
                        lambda ep: all(tid in _report_task_ids(ep) for tid in ("TASK035", "TASK042", "TASK044", "TASK048", "TASK051", "TASK052")),
                        True,
                        weight=2.0,
                    ),
                    StateExpectation(
                        "handover_report_articulates_status",
                        lambda ep: any(w in _report_summary(ep).upper() for w in ("BLOCKED", "READY", "CUTOVER", "BLOCKER")),
                        True,
                        weight=1.5,
                    ),
                ),
            ),
        ),
        milestones=(
            EventVerifier(
                required=MILESTONE_EVENTS,
                weights=_EVENT_WEIGHTS,
            ),
            TemporalVerifier(
                orderings=(
                    Ordering("release_audit_inspected", "circular_dep_broken"),
                    Ordering("circular_dep_broken", "task048_completed"),
                    Ordering("task048_completed", "task044_completed"),
                    Ordering("handover_reported", "reconciliation_complete"),
                ),
                answer_after=(
                    "task048_completed", "task044_completed", "compliance_unblocked",
                    "race_reassigned", "task051_deduplicated", "task052_deduplicated",
                ),
                answer_seq=lambda ep: (
                    max((a.seq for a in ep.actions_with("submit_handover_report")), default=None)
                ),
            ),
        ),
        trajectory=(
            TrajectoryVerifier(
                necessary=(
                    ToolExpectation(
                        "audited_before_acting",
                        _enumerated_first,
                        "Tasks in the release project were inspected before making mutations.",
                        weight=2.0,
                    ),
                ),
                action_penalties=(
                    ActionPenalty(
                        "off_target_mutation",
                        _off_target_actions,
                        amount_per_action=0.1,
                        description="Mutations performed on tasks outside the release reconciliation target scope.",
                    ),
                ),
            ),
        ),
        negative=(
            NegativeVerifier(
                forbidden=(
                    Forbidden(
                        "changed_unrelated_tasks",
                        _unrelated_changes,
                        "Tasks outside the release reconciliation scope were modified.",
                    ),
                    Forbidden(
                        "sandbox_escape_detected",
                        _escape_attempts,
                        "Attempted sandbox escape or unprivileged actor impersonation.",
                    ),
                ),
            ),
        ),
        milestone_events=MILESTONE_EVENTS,
        metadata={
            "project_id": RELEASE_PROJECT,
            "milestone_id": CUTOVER_MILESTONE,
            "target_tasks": list(RECONCILIATION_TARGET_TASKS),
        },
    )


__all__ = ["CONTRACT_NAME", "MILESTONE_EVENTS", "build_contract"]
