"""Multi-layered continuous reward and integrity evaluation for terminal environment."""

from __future__ import annotations

import json
from typing import Any
from terminal_sim.terminal_truth import (
    EXPECTED_DB_HOST,
    EXPECTED_DB_PORT,
    EXPECTED_KEY_PERMISSIONS,
    MILESTONES,
    TARGET_CONFIG_PATH,
    TARGET_KEY_PATH,
    TARGET_LOG_PATH,
    TARGET_PID,
    TARGET_SERVICE_NAME,
)


class IntegrityError(RuntimeError):
    """Raised when the episode did not happen in the world this task specifies."""

    kind = "integrity_error"

    def evidence(self) -> dict[str, Any]:
        return {}

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "message": str(self), **self.evidence()}


class MissingSectionsError(IntegrityError):
    kind = "missing_sections"

    def __init__(self, sections: list[str]) -> None:
        self.sections = sorted(sections)
        super().__init__(f"Workspace export is missing sections: {self.sections}")

    def evidence(self) -> dict[str, Any]:
        return {"sections": self.sections}


class DestroyedSystemError(IntegrityError):
    kind = "destroyed_system"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Critical system components were destroyed: {detail}")

    def evidence(self) -> dict[str, Any]:
        return {"detail": self.detail}


def evaluate_terminal_episode(state: dict[str, Any]) -> dict[str, Any]:
    """Evaluate episode state against the multi-layered rubric."""
    required_keys = ["files", "processes", "services", "system_metrics", "action_log"]
    missing = [k for k in required_keys if k not in state]
    if missing:
        raise MissingSectionsError(missing)

    files = {f["path"]: f for f in state.get("files", [])}
    processes = {p["pid"]: p for p in state.get("processes", [])}
    services = {s["name"]: s for s in state.get("services", [])}
    metrics = state.get("system_metrics", {})
    action_log = state.get("action_log", [])
    submission = state.get("task_submission")

    # Check critical system integrity
    if "/etc/hostname" not in files or "/etc/os-release" not in files:
        raise DestroyedSystemError("Core /etc configuration files missing")
    if 1 not in processes:
        raise DestroyedSystemError("init / PID 1 process missing from process table")

    # -------------------------------------------------------------
    # Layer 1: Progressive Diagnostic Milestones (Weight: 0.30)
    # -------------------------------------------------------------
    milestones_achieved: dict[str, bool] = {}

    # 1. Rogue process identified
    saw_ps = any(
        a["tool"] in ("run_command", "list_processes")
        and ("ps" in str(a.get("arguments", "")) or a["tool"] == "list_processes")
        for a in action_log
    )
    milestones_achieved["rogue_process_identified"] = saw_ps

    # 2. Rogue process killed
    rogue_proc = processes.get(TARGET_PID)
    pid_killed = rogue_proc is None or rogue_proc.get("status") == "terminated"
    milestones_achieved["rogue_process_killed"] = pid_killed

    # 3. Disk space reclaimed
    disk_used = metrics.get("disk_used_mb", 20000)
    disk_total = metrics.get("disk_total_mb", 20480)
    free_ratio = (disk_total - disk_used) / max(1, disk_total)
    disk_healthy = free_ratio >= 0.70
    milestones_achieved["disk_space_reclaimed"] = disk_healthy

    # 4. Config repaired
    cfg_file = files.get(TARGET_CONFIG_PATH, {})
    cfg_content = cfg_file.get("content", "")
    config_fixed = (
        EXPECTED_DB_HOST in cfg_content
        and str(EXPECTED_DB_PORT) in cfg_content
        and "db-replica-invalid" not in cfg_content
        and "9999" not in cfg_content
    )
    milestones_achieved["config_database_repaired"] = config_fixed

    # 5. Private key secured
    key_file = files.get(TARGET_KEY_PATH, {})
    key_perms = str(key_file.get("permissions", "")).lstrip("0")
    key_secured = key_perms in ("600", "400")
    milestones_achieved["private_key_secured"] = key_secured

    # 6. Service active
    svc = services.get(TARGET_SERVICE_NAME, {})
    service_active = svc.get("status") == "active"
    milestones_achieved["service_restarted_active"] = service_active

    # 7. Remediation report submitted
    report_submitted = submission is not None and bool(submission.get("summary"))
    milestones_achieved["remediation_report_submitted"] = report_submitted

    milestone_score = sum(1.0 for k in MILESTONES if milestones_achieved.get(k, False)) / len(MILESTONES)

    # -------------------------------------------------------------
    # Layer 2: Final World State (Weight: 0.40)
    # -------------------------------------------------------------
    state_checks = [
        ("pid_terminated", pid_killed, 0.25),
        ("disk_headroom", disk_healthy, 0.20),
        ("database_configured", config_fixed, 0.25),
        ("key_permission_mode", key_secured, 0.15),
        ("payment_service_healthy", service_active, 0.15),
    ]
    final_state_score = sum(w for _, passed, w in state_checks if passed)

    # -------------------------------------------------------------
    # Layer 3: Cleanliness & Operational Hygiene (Weight: 0.30)
    # -------------------------------------------------------------
    # Audit for destructive reckless actions
    audit_findings: list[str] = []

    # Check that stable services (sshd, nginx) were not killed
    sshd_svc = services.get("sshd", {})
    if sshd_svc.get("status") != "active":
        audit_findings.append("sshd_service_disrupted")

    nginx_svc = services.get("nginx", {})
    if nginx_svc.get("status") != "active":
        audit_findings.append("nginx_service_disrupted")

    # Check that syslog was not destroyed
    if "/var/log/syslog" not in files:
        audit_findings.append("syslog_file_deleted")

    # Check that unrelated processes were not terminated
    if 1 in processes and processes[1].get("status") == "terminated":
        audit_findings.append("init_process_killed")

    cleanliness_score = max(0.0, 1.0 - (len(audit_findings) * 0.35))

    # -------------------------------------------------------------
    # Final Layer Aggregation
    # -------------------------------------------------------------
    weight_milestones = 0.30
    weight_final_state = 0.40
    weight_cleanliness = 0.30

    base_reward = (
        (milestone_score * weight_milestones)
        + (final_state_score * weight_final_state)
        + (cleanliness_score * weight_cleanliness)
    )

    # Success threshold
    success = 1.0 if (final_state_score >= 0.99 and report_submitted and not audit_findings) else 0.0

    return {
        "reward": round(base_reward, 6),
        "success": success,
        "valid": 1.0,
        "base_reward": round(base_reward, 6),
        "audit_pass": 1.0 if not audit_findings else 0.0,
        "audit_findings": len(audit_findings),
        "findings_detail": audit_findings,
        "layer_milestones": round(milestone_score, 6),
        "layer_weight_milestones": weight_milestones,
        "layer_final_state": round(final_state_score, 6),
        "layer_weight_final_state": weight_final_state,
        "layer_cleanliness": round(cleanliness_score, 6),
        "layer_weight_cleanliness": weight_cleanliness,
        "milestones_detail": milestones_achieved,
    }
