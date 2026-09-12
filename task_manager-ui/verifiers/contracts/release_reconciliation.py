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
    "release_audit_inspected": 1.0,
    "circular_dep_broken": 2.0,
    "task048_completed": 1.5,
    "task044_completed": 1.5,
    "compliance_unblocked": 1.5,
    "race_reassigned": 1.5,
    "task051_deduplicated": 1.0,
    "task052_deduplicated": 1.0,
    "rehearsal_dryrun_failed": 2.0,
    "replica_patch_available": 2.0,
    "task056_resolved": 2.5,
    "task057_resolved": 2.0,
    "final_rehearsal_executed": 2.5,
    "external_blocker_inspected": 2.0,
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
    if not report:
        return ""
    return str(report.get("summary") or "")


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


def _prerequisite_observed_before_unblock(episode: Episode) -> bool:
    read_ts = [
        float(a.ts) for a in episode.agent_actions
        if a.tool in ("get_task", "search_tasks") and a.task_id == "TASK047"
    ]
    unblock_ts = [
        float(a.ts) for a in episode.agent_actions
        if a.tool == "update_task" and a.task_id == "TASK035"
    ]
    if not unblock_ts:
        return False
    if not read_ts:
        return False
    return min(read_ts) <= min(unblock_ts)


def _external_blocker_observed_before_report(episode: Episode) -> bool:
    read_ts = [
        float(a.ts) for a in episode.agent_actions
        if a.tool in ("get_task", "list_comments", "search_tasks") and a.task_id == "TASK058"
    ]
    report_ts = [
        float(a.ts) for a in episode.agent_actions
        if a.tool == "submit_handover_report"
    ]
    if not report_ts or not read_ts:
        return False
    return min(read_ts) <= min(report_ts)


def _verification_comment_on_incident(episode: Episode) -> bool:
    return any(
        a.tool == "add_comment" and a.task_id == "TASK056"
        for a in episode.agent_actions
    )


def _off_target_actions(episode: Episode) -> list[str]:
    off_target: list[str] = []
    for action in episode.agent_actions:
        if action.tool in ("create_project", "create_milestone"):
            off_target.append(f"{action.tool}")
        elif (
            action.tool in ("update_task", "move_task_to_project", "link_tasks", "unlink_tasks", "mark_task_duplicate", "add_comment")
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
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task044_is_completed",
                        lambda ep: (ep.task("TASK044") or {}).get("status"),
                        "COMPLETED",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task035_is_completed",
                        lambda ep: (ep.task("TASK035") or {}).get("status"),
                        "COMPLETED",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task042_assignee_is_marcus",
                        lambda ep: (ep.task("TASK042") or {}).get("assignee_id"),
                        "U008",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task042_priority_is_urgent",
                        lambda ep: (ep.task("TASK042") or {}).get("priority"),
                        "URGENT",
                        weight=1.0,
                    ),
                    StateExpectation(
                        "task051_is_duplicate",
                        lambda ep: (ep.task("TASK051") or {}).get("status"),
                        "DUPLICATE",
                        weight=1.0,
                    ),
                    StateExpectation(
                        "task052_is_duplicate",
                        lambda ep: (ep.task("TASK052") or {}).get("status"),
                        "DUPLICATE",
                        weight=1.0,
                    ),
                    StateExpectation(
                        "circular_dependency_removed",
                        lambda ep: _dependency_exists(ep, "TASK048", "TASK044"),
                        False,
                        weight=2.0,
                    ),
                    StateExpectation(
                        "task056_is_completed",
                        lambda ep: (ep.task("TASK056") or {}).get("status"),
                        "COMPLETED",
                        weight=2.0,
                    ),
                    StateExpectation(
                        "task056_has_verification_comment",
                        lambda ep: any(c.get("task_id") == "TASK056" and c.get("author_id") == "U001" for c in ep.state.get("comments", [])),
                        True,
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task057_is_completed",
                        lambda ep: (ep.task("TASK057") or {}).get("status"),
                        "COMPLETED",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "task058_is_blocked",
                        lambda ep: (ep.task("TASK058") or {}).get("status"),
                        "BLOCKED",
                        weight=1.5,
                    ),
                    StateExpectation(
                        "handover_report_lists_reconciled_tasks",
                        lambda ep: all(
                            tid in _report_task_ids(ep)
                            for tid in ("TASK035", "TASK042", "TASK044", "TASK048", "TASK051", "TASK052", "TASK056", "TASK057", "TASK058")
                        ),
                        True,
                        weight=2.5,
                    ),
                    StateExpectation(
                        "handover_report_articulates_status",
                        lambda ep: (
                            any(w in _report_summary(ep).upper() for w in ("BLOCKED", "NO-GO", "NOGO"))
                            and any(w in _report_summary(ep).lower() for w in ("paycore", "payment", "maintenance", "window", "conflict"))
                        ),
                        True,
                        weight=2.5,
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
                    Ordering("task048_completed", "rehearsal_dryrun_failed"),
                    Ordering("rehearsal_dryrun_failed", "replica_patch_available"),
                    Ordering("replica_patch_available", "task056_resolved"),
                    Ordering("task056_resolved", "final_rehearsal_executed"),
                    Ordering("final_rehearsal_executed", "external_blocker_inspected"),
                    Ordering("external_blocker_inspected", "handover_reported"),
                    Ordering("handover_reported", "reconciliation_complete"),
                ),
                answer_after=(
                    "task048_completed", "task044_completed", "compliance_unblocked",
                    "race_reassigned", "task051_deduplicated", "task052_deduplicated",
                    "task056_resolved", "task057_resolved", "final_rehearsal_executed",
                    "external_blocker_inspected",
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
                    ToolExpectation(
                        "prerequisite_observed_before_unblock",
                        _prerequisite_observed_before_unblock,
                        "Vendor attestation TASK047 was observed before clearing compliance hold on TASK035.",
                        weight=1.5,
                    ),
                    ToolExpectation(
                        "external_blocker_observed_before_report",
                        _external_blocker_observed_before_report,
                        "External blocker TASK058 was observed before submitting the handover report.",
                        weight=1.5,
                    ),
                    ToolExpectation(
                        "verification_comment_on_incident",
                        _verification_comment_on_incident,
                        "A verification comment was posted on incident TASK056 confirming replica lag SLA.",
                        weight=1.5,
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
