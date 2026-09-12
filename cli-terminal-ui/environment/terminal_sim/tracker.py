"""Event tracker and reactive scenario engine for terminal environment.

Observability and rule evaluation:
- Records all actions to `action_log`.
- Evaluates scenario rules against actions and updates latent world states.
- Generates structured EventTrace diagnostics for attributing agent behavior.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any
from terminal_sim.clock import VIRTUAL_CLOCK


@dataclass(frozen=True, slots=True)
class Predicate:
    name: str
    passed: bool
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    rule_id: str
    trigger: str
    passed: bool
    predicates: list[Predicate]
    effect: str


class TerminalTracker:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def record_action(
        self,
        tool: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        actor: str = "admin",
    ) -> list[RuleEvaluation]:
        now = VIRTUAL_CLOCK.now()
        args_json = json.dumps(arguments, default=str)
        result_json = json.dumps(result, default=str)

        self.conn.execute(
            """
            INSERT INTO action_log (timestamp, tool, arguments, result, actor)
            VALUES (?, ?, ?, ?, ?)
            """,
            (now, tool, args_json, result_json, actor),
        )

        evaluations = self._evaluate_scenario_rules(tool, arguments, result, now)
        self.conn.commit()
        return evaluations

    def _evaluate_scenario_rules(
        self,
        tool: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        now: float,
    ) -> list[RuleEvaluation]:
        evaluations: list[RuleEvaluation] = []
        rules = self.conn.execute(
            "SELECT rule_id, trigger, condition, effect, activated FROM scenario_rules WHERE activated = 0"
        ).fetchall()

        for rule in rules:
            rule_id = rule["rule_id"]
            trigger = rule["trigger"]
            condition = rule["condition"]
            effect = rule["effect"]

            preds: list[Predicate] = []
            passed = False

            if trigger == "kill" and (tool == "run_command" or tool == "kill_process"):
                cmd = str(arguments.get("command", ""))
                target_pid = "4921" in cmd or arguments.get("pid") == 4921 or "worker-leak" in cmd
                pred = Predicate("target_pid_matched", target_pid, {"cmd": cmd})
                preds.append(pred)
                passed = target_pid

            elif trigger == "truncate" and (tool == "run_command" or tool == "write_file"):
                cmd = str(arguments.get("command", ""))
                path = str(arguments.get("path", ""))
                is_target = "/var/log/app/debug_trace.log" in cmd or "/var/log/app/debug_trace.log" in path
                pred = Predicate("log_target_matched", is_target, {"cmd": cmd, "path": path})
                preds.append(pred)
                passed = is_target

            elif trigger == "write_file" and (tool == "write_file" or tool == "run_command"):
                cmd = str(arguments.get("command", ""))
                path = str(arguments.get("path", ""))
                is_cfg = "config.yaml" in cmd or "config.yaml" in path
                pred = Predicate("config_path_matched", is_cfg, {"path": path, "cmd": cmd})
                preds.append(pred)
                passed = is_cfg

            elif trigger == "chmod" and (tool == "run_command" or tool == "change_permissions"):
                cmd = str(arguments.get("command", ""))
                path = str(arguments.get("path", ""))
                is_key = "payment-api.key" in cmd or "payment-api.key" in path
                is_strict = "600" in cmd or "400" in cmd or arguments.get("permissions") in ("0600", "0400")
                pred1 = Predicate("key_path_matched", is_key)
                pred2 = Predicate("mode_strict_matched", is_strict)
                preds.extend([pred1, pred2])
                passed = is_key and is_strict

            elif trigger == "systemctl" and tool == "run_command":
                cmd = str(arguments.get("command", ""))
                is_restart = "restart" in cmd and "payment-processor" in cmd
                pred = Predicate("service_restarted", is_restart, {"cmd": cmd})
                preds.append(pred)
                passed = is_restart

            eval_res = RuleEvaluation(rule_id, trigger, passed, preds, effect)
            evaluations.append(eval_res)

            # Record event trace
            self.conn.execute(
                """
                INSERT INTO event_traces (timestamp, event_id, rule_id, result, detail)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    now,
                    f"evt_{rule_id}_{int(now)}",
                    rule_id,
                    "ACTIVATED" if passed else "SKIPPED",
                    json.dumps([{"name": p.name, "passed": p.passed, "detail": p.detail} for p in preds]),
                ),
            )

            if passed:
                self.conn.execute(
                    "UPDATE scenario_rules SET activated = 1 WHERE rule_id = ?",
                    (rule_id,),
                )

        return evaluations
