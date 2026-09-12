"""Gymnasium-compatible reinforcement learning environment for Terminal."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from terminal_sim.seed import seed_database
from terminal_sim.service import TerminalService, export_state
from terminal_sim.sqlite_common import init_db
from terminal_sim.terminal_reward import evaluate_terminal_episode


class TerminalRLEnv:
    """RL environment wrapper for the terminal incident remediation task."""

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self.db_path = db_path
        self.conn = init_db(db_path)
        self.service = TerminalService(self.conn)
        self._step_count = 0
        self._max_steps = 100
        self.reset()

    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        self.conn = seed_database(self.db_path)
        self.service = TerminalService(self.conn)
        self._step_count = 0
        state = export_state(self.conn)
        return state, {"step_count": 0}

    def step(self, action: dict[str, Any]) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        self._step_count += 1
        tool = action.get("tool", "run_command")
        args = action.get("args", {})

        result = self.service.execute_tool(tool, args)
        state = export_state(self.conn)

        eval_res = evaluate_terminal_episode(state)
        reward = float(eval_res["reward"])
        terminated = bool(eval_res["success"] == 1.0 or tool == "submit_task")
        truncated = self._step_count >= self._max_steps

        info = {
            "eval": eval_res,
            "result": result,
            "step": self._step_count,
        }
        return state, reward, terminated, truncated, info

    def close(self) -> None:
        if self.conn:
            self.conn.close()
