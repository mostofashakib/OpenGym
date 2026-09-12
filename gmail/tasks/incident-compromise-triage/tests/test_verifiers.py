"""Tests for Gmail verifiers and Harbor reward stream."""

from __future__ import annotations

import unittest

from verifiers.harbor import blank_reward_dict, reward_dict, reward_keys
from verifiers.results import (
    CheckOutcome,
    EpisodeEvaluation,
    LayerBreakdown,
    LayerScore,
)


class TestVerifiers(unittest.TestCase):
    def test_blank_reward_keys(self) -> None:
        blank = blank_reward_dict(valid=0.0)
        for k in reward_keys():
            self.assertIn(k, blank)
        self.assertEqual(blank["valid"], 0.0)
        self.assertEqual(blank["reward"], 0.0)

    def test_reward_dict_evaluation(self) -> None:
        eval_res = EpisodeEvaluation(
            reward=1.0,
            passed=True,
            valid=True,
            breakdown=LayerBreakdown(
                base=1.0,
                penalty_total=0.0,
                layers=(
                    LayerScore("task_actions", 1.0, 0.5),
                    LayerScore("final_state", 1.0, 0.3),
                    LayerScore("cleanliness", 1.0, 0.2),
                ),
            ),
            checks=(
                CheckOutcome("test_check_1", True),
                CheckOutcome("test_check_2", True),
            ),
            penalties=(),
        )

        r = reward_dict(eval_res)
        self.assertEqual(r["reward"], 1.0)
        self.assertEqual(r["success"], 1.0)
        self.assertEqual(r["valid"], 1.0)
        self.assertEqual(r["layer_task_actions"], 1.0)
        self.assertEqual(r["layer_final_state"], 1.0)
        self.assertEqual(r["layer_cleanliness"], 1.0)


if __name__ == "__main__":
    unittest.main()
