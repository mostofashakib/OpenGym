"""Event tracker and reactive scenario engine for browser environment."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any
from browser_sim.clock import VIRTUAL_CLOCK


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


class BrowserTracker:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def record_action(
        self,
        tool: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        actor: str = "audit-officer",
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
            effect = rule["effect"]
            passed = False
            preds: list[Predicate] = []

            if trigger == "reject_order":
                el = str(arguments.get("element_id", ""))
                is_rej = "reject-po-9821" in el or "PO-9821" in str(result)
                pred = Predicate("reject_fraud_order", is_rej, {"element_id": el})
                preds.append(pred)
                passed = is_rej

            elif trigger == "approve_order":
                el = str(arguments.get("element_id", ""))
                is_app = "approve-po-3410" in el or "PO-3410" in str(result)
                pred = Predicate("approve_renewal_order", is_app, {"element_id": el})
                preds.append(pred)
                passed = is_app

            elif trigger == "update_vendor":
                el = str(arguments.get("element_id", ""))
                is_bl = "blacklist-vend-ghostwire" in el or "VEND-GHOSTWIRE" in str(result)
                pred = Predicate("blacklist_shell_vendor", is_bl, {"element_id": el})
                preds.append(pred)
                passed = is_bl

            elif trigger == "compliance_filing":
                el = str(arguments.get("element_id", "")) or str(arguments.get("form_id", ""))
                is_filing = "compliance" in el or "SOC2-2026-NEXUS-778" in str(arguments.get("text", "")) or "SOC2-2026-NEXUS-778" in str(result)
                pred = Predicate("compliance_filing_submitted", is_filing)
                preds.append(pred)
                passed = is_filing

            eval_res = RuleEvaluation(rule_id, trigger, passed, preds, effect)
            evaluations.append(eval_res)

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
