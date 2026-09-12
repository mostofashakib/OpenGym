"""Unit tests for terminal verifier."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from terminal_sim.seed import seed_database
from terminal_sim.service import export_state
from terminal_sim.terminal_reward import evaluate_terminal_episode
from verifiers.layered import evaluate_episode


class TestVerifiers(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_verifiers.db"
        self.conn = seed_database(self.db_path)

    def tearDown(self) -> None:
        self.conn.close()
        self.temp_dir.cleanup()

    def test_initial_unresolved_score(self) -> None:
        state = export_state(self.conn)
        res = evaluate_terminal_episode(state)
        self.assertEqual(res["success"], 0.0)
        self.assertTrue(res["valid"] == 1.0)
        self.assertLess(res["reward"], 0.5)

    def test_layered_eval(self) -> None:
        state = export_state(self.conn)
        eval_res = evaluate_episode(state_data=state)
        self.assertEqual(eval_res.valid, 1.0)
        self.assertEqual(eval_res.success, 0.0)


if __name__ == "__main__":
    unittest.main()
