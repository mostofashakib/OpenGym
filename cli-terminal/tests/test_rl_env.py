import unittest
try:
    from rl_env import TerminalRLEnv
except ImportError:
    from environment.rl_env import TerminalRLEnv


class TestTerminalRLEnv(unittest.TestCase):
    def test_env_lifecycle(self) -> None:
        env = TerminalRLEnv(":memory:")
        obs, info = env.reset()
        self.assertIn("files", obs)
        self.assertIn("processes", obs)

        # Step: ps
        obs, reward, term, trunc, info = env.step({"tool": "run_command", "args": {"command": "ps aux"}})
        self.assertFalse(term)
        self.assertFalse(trunc)
        self.assertGreaterEqual(reward, 0.0)

        # Step: kill rogue process
        obs, reward, term, trunc, info = env.step({"tool": "run_command", "args": {"command": "kill -9 4921"}})
        self.assertFalse(term)
        self.assertGreater(reward, 0.0)

        env.close()


if __name__ == "__main__":
    unittest.main()
