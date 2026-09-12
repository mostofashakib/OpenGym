"""Tests for agent provider adapters and schema rendering in terminal."""

from __future__ import annotations

import unittest

from agent.config import AgentConfig
from agent.harbor_agent import TerminalAgent
from agent.providers import (
    AnthropicProvider,
    CompatibleAPIProvider,
    OllamaProvider,
    OpenRouterProvider,
    build_provider,
)
from agent.schemas import build_action_schema
from tools.tool_definitions import get_tool_definitions


class TestAgentAdapters(unittest.TestCase):
    def test_provider_factory(self) -> None:
        p1 = build_provider("ollama/qwen3.6:35b")
        self.assertIsInstance(p1, OllamaProvider)
        self.assertEqual(p1.model, "qwen3.6:35b")
        self.assertEqual(p1.provider_name, "ollama")

        p2 = build_provider("openrouter/anthropic/claude-opus-5")
        self.assertIsInstance(p2, OpenRouterProvider)
        self.assertEqual(p2.model, "anthropic/claude-opus-5")

        p3 = build_provider("anthropic/claude-3-5-sonnet")
        self.assertIsInstance(p3, AnthropicProvider)

    def test_schema_generation(self) -> None:
        tools = get_tool_definitions()
        schema = build_action_schema(tools)
        self.assertIn("properties", schema)
        self.assertIn("actions", schema["properties"])

    def test_agent_config(self) -> None:
        cfg = AgentConfig.from_env(model="ollama/qwen3.6:35b", max_turns=20)
        self.assertEqual(cfg.model, "ollama/qwen3.6:35b")
        self.assertEqual(cfg.max_turns, 20)

    def test_terminal_agent_init(self) -> None:
        agent = TerminalAgent(logs_dir=None, model_name="ollama/qwen3.6:35b")
        self.assertEqual(agent.name(), "terminal-adapter")


if __name__ == "__main__":
    unittest.main()
