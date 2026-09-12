"""State checks for browser environment verification."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from browser_sim.browser_reward import evaluate_browser_episode
from verifiers.results import CheckOutcome


def _load_state(client: Any | None = None, state_data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if state_data is not None:
        return state_data

    # 1. Try sockets
    for sock in [
        os.environ.get("BROWSER_ADMIN_SOCKET", "/run/browser/admin.sock"),
        os.environ.get("BROWSER_SOCKET", "/run/browser/agent.sock"),
    ]:
        if os.path.exists(sock):
            try:
                from browser_sim.protocol import request
                resp = request(sock, {"op": "export_state"})
                if resp.get("ok") and "result" in resp:
                    return resp["result"]
            except Exception:
                pass

    # 2. Try export artifact
    for candidate in [
        Path("/var/lib/browser/state-export.json"),
        Path("/tmp/state-export.json"),
        Path("state-export.json"),
    ]:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                pass

    # 3. Try direct SQLite database
    for db_candidate in [
        Path("/var/lib/browser/browser.db"),
        Path("/tmp/test_browser.db"),
        Path("browser.db"),
    ]:
        if db_candidate.exists():
            try:
                from browser_sim.service import export_state
                from browser_sim.sqlite_common import get_connection

                with get_connection(db_candidate) as conn:
                    return export_state(conn)
            except Exception:
                pass

    if client is not None:
        try:
            res = client.get_state()
            if res.get("ok"):
                return res.get("result", {})
        except Exception:
            pass

    return None


def evaluate_browser_checks(
    client: Any | None = None,
    state_data: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[CheckOutcome]]:
    state = _load_state(client, state_data)
    if state is None:
        return {}, [
            CheckOutcome(
                name="state_fetchable",
                passed=False,
                detail={"error": "Could not retrieve browser state from socket, artifact, or database"},
                weight=1.0,
            )
        ]

    eval_dict = evaluate_browser_episode(state)
    checks: list[CheckOutcome] = []

    milestones = eval_dict.get("milestones_detail", {})
    for m_name, m_passed in milestones.items():
        checks.append(CheckOutcome(name=f"milestone_{m_name}", passed=m_passed, weight=0.1))

    checks.append(
        CheckOutcome(
            name="final_state_score",
            passed=eval_dict.get("layer_final_state", 0.0) >= 0.99,
            detail={"score": eval_dict.get("layer_final_state")},
            weight=0.4,
        )
    )
    checks.append(
        CheckOutcome(
            name="cleanliness_audit",
            passed=eval_dict.get("audit_pass", 0.0) == 1.0,
            detail={"findings": eval_dict.get("findings_detail", [])},
            weight=0.3,
        )
    )

    return eval_dict, checks
