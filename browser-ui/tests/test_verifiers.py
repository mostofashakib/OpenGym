"""Unit tests for browser verifier."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from browser_sim.browser_reward import evaluate_browser_episode
from browser_sim.seed import seed_database
from browser_sim.service import export_state
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
        res = evaluate_browser_episode(state)
        self.assertEqual(res["success"], 0.0)
        self.assertEqual(res["valid"], 1.0)
        self.assertLess(res["reward"], 0.5)

    def test_layered_eval(self) -> None:
        state = export_state(self.conn)
        eval_res = evaluate_episode(state_data=state)
        self.assertEqual(eval_res.valid, 1.0)
        self.assertEqual(eval_res.success, 0.0)


if __name__ == "__main__":
    unittest.main()
