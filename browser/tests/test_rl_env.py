"""Tests for browser RL environment wrapper."""

from __future__ import annotations

import unittest
try:
    from rl_env import BrowserRLEnv
except ImportError:
    from environment.rl_env import BrowserRLEnv


class TestBrowserRLEnv(unittest.TestCase):
    def test_env_lifecycle(self) -> None:
        env = BrowserRLEnv(":memory:")
        obs, info = env.reset()
        self.assertIn("orders", obs)
        self.assertIn("vendors", obs)

        # Step: get page
        obs, reward, term, trunc, info = env.step({"tool": "get_page", "args": {}})
        self.assertFalse(term)
        self.assertFalse(trunc)
        self.assertGreaterEqual(reward, 0.0)

        # Step: navigate to orders
        obs, reward, term, trunc, info = env.step({"tool": "navigate", "args": {"url": "/orders"}})
        self.assertFalse(term)
        self.assertGreater(reward, 0.0)

        env.close()


if __name__ == "__main__":
    unittest.main()
