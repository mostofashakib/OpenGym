"""Tests for agent provider adapters in browser."""

from __future__ import annotations

import unittest

from agent.config import AgentConfig
from agent.harbor_agent import BrowserAgent
from agent.providers import (
    AnthropicProvider,
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

        p2 = build_provider("openrouter/anthropic/claude-opus-5")
        self.assertIsInstance(p2, OpenRouterProvider)

        p3 = build_provider("anthropic/claude-3-5-sonnet")
        self.assertIsInstance(p3, AnthropicProvider)

    def test_schema_generation(self) -> None:
        tools = get_tool_definitions()
        schema = build_action_schema(tools)
        self.assertIn("properties", schema)
        self.assertIn("actions", schema["properties"])

    def test_browser_agent_init(self) -> None:
        agent = BrowserAgent(logs_dir=None, model_name="ollama/qwen3.6:35b")
        self.assertEqual(agent.name(), "browser-adapter")


if __name__ == "__main__":
    unittest.main()
