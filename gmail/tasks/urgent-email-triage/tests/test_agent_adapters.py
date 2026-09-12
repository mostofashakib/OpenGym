"""Tests for agent provider adapters and schema rendering."""

from __future__ import annotations

import unittest

from agent.config import AgentConfig
from agent.harbor_agent import GmailAgent
from agent.providers import (
    AnthropicProvider,
    CompatibleAPIProvider,
    OllamaProvider,
    OpenRouterProvider,
    ProviderAdapterRegistry,
    ProviderRegistry,
    build_provider,
    register_provider,
)
from agent.schemas import build_action_schema, strict_parameters
from agent.tracker import ObservabilityTracker
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
        self.assertEqual(p2.provider_name, "openrouter")

        p3 = build_provider("anthropic/claude-3-5-sonnet")
        self.assertIsInstance(p3, AnthropicProvider)
        self.assertEqual(p3.model, "claude-3-5-sonnet")
        self.assertEqual(p3.provider_name, "anthropic")

        p4 = build_provider("compatible/local-llama")
        self.assertIsInstance(p4, CompatibleAPIProvider)
        self.assertEqual(p4.model, "local-llama")
        self.assertEqual(p4.provider_name, "compatible")

        # Bare model defaults to Ollama
        p5 = build_provider("llama3")
        self.assertIsInstance(p5, OllamaProvider)
        self.assertEqual(p5.model, "llama3")

    def test_provider_adapter_registry_switching(self) -> None:
        # Default without args resolves cleanly to Ollama
        p_def = build_provider()
        self.assertIsInstance(p_def, OllamaProvider)
        self.assertEqual(p_def.provider_name, "ollama")
        self.assertEqual(p_def.model, "qwen3.6:35b")
        self.assertEqual(p_def.spec, "ollama/qwen3.6:35b")

        # Switching by provider name alone
        p_ant = build_provider("anthropic")
        self.assertIsInstance(p_ant, AnthropicProvider)
        self.assertEqual(p_ant.provider_name, "anthropic")
        self.assertEqual(p_ant.model, "claude-3-5-sonnet-20241022")

        p_open = build_provider("openrouter")
        self.assertIsInstance(p_open, OpenRouterProvider)
        self.assertEqual(p_open.provider_name, "openrouter")

        # Registry list
        providers = ProviderRegistry.available_providers()
        self.assertIn("ollama", providers)
        self.assertIn("anthropic", providers)
        self.assertIn("openrouter", providers)
        self.assertIn("compatible", providers)

    def test_agent_config(self) -> None:
        cfg = AgentConfig.from_env(model="ollama/mistral:7b", max_turns=25)
        self.assertEqual(cfg.model, "ollama/mistral:7b")
        self.assertEqual(cfg.provider_name, "ollama")
        self.assertEqual(cfg.model_name, "mistral:7b")
        self.assertEqual(cfg.max_turns, 25)
        prov = cfg.build_provider()
        self.assertIsInstance(prov, OllamaProvider)

        # Config switching provider by provider name
        cfg2 = AgentConfig.from_env(model="anthropic")
        self.assertEqual(cfg2.provider_name, "anthropic")
        prov2 = cfg2.build_provider()
        self.assertIsInstance(prov2, AnthropicProvider)

    def test_harbor_agent_adapter_spec(self) -> None:
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            logs = Path(tmpdir)
            agent = GmailAgent(logs_dir=logs, model_name="anthropic/claude-3-5-haiku")
            self.assertEqual(agent._provider.spec, "anthropic/claude-3-5-haiku")

            traj = json.loads((logs / "trajectory.json").read_text())
            self.assertEqual(traj["model_name"], "anthropic/claude-3-5-haiku")

    def test_observability_tracker(self) -> None:
        import tempfile
        from pathlib import Path

        tracker = ObservabilityTracker(session_id="obs-test", provider="ollama", model="qwen3.6:35b")
        tracker.start_run("Test instruction")
        tracker.start_turn(1)
        tracker.record_llm_call(1, prompt_tokens=100, completion_tokens=20, latency_sec=0.1)
        tracker.record_tool_call(
            turn_index=1,
            call_id="c1",
            tool_name="list_emails",
            arguments={"query": "test"},
            result={"ok": True},
            latency_sec=0.02,
            ok=True,
        )
        tracker.end_turn(1, stop_reason="finished")
        tracker.finish_run("completed")

        summary = tracker.summary()
        self.assertEqual(summary["total_turns"], 1)
        self.assertEqual(summary["tokens"]["prompt_tokens"], 100)
        self.assertEqual(summary["tools"]["total_calls"], 1)

        with tempfile.TemporaryDirectory() as tmpdir:
            p = tracker.export_json(Path(tmpdir) / "obs.json")
            self.assertTrue(p.exists())

        dashboard = tracker.render_ascii_dashboard()
        self.assertIn("OBSERVABILITY REPORT", dashboard)
        self.assertIn("list_emails", dashboard)

    def test_strict_parameters(self) -> None:
        tools = get_tool_definitions()
        for t in tools:
            schema = t.get("input_schema")
            strict = strict_parameters(schema)
            self.assertFalse(strict.get("additionalProperties"))
            props = strict.get("properties", {})
            req = strict.get("required", [])
            for p in props:
                self.assertIn(p, req)

    def test_action_schema_structure(self) -> None:
        tools = get_tool_definitions()
        action_schema = build_action_schema(tools)
        self.assertEqual(action_schema.get("type"), "object")
        props = action_schema.get("properties", {})
        self.assertIn("actions", props)
        self.assertIn("thought", props)
        self.assertIn("answer", props)

    def test_action_schema_with_string_tool_names(self) -> None:
        from agent.backends import _normalize_tool_definitions
        from agent.schemas import render_catalogue
        string_tools = ["list_emails", "get_email", "unknown_tool"]
        schema = build_action_schema(string_tools)
        self.assertEqual(schema.get("type"), "object")
        cat = render_catalogue(string_tools)
        self.assertIn("list_emails", cat)

        norm = _normalize_tool_definitions(string_tools)
        self.assertEqual(len(norm), 3)
        self.assertEqual(norm[0]["name"], "list_emails")
        self.assertIn("properties", norm[0]["input_schema"])


if __name__ == "__main__":
    unittest.main()
