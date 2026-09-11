"""Agent configuration dataclass with provider adapter integration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from agent.providers import ProviderAdapter, ProviderRegistry, build_provider


@dataclass(slots=True)
class AgentConfig:
    model: str = field(default_factory=ProviderRegistry.default_spec)
    prompt_id: str = "default"
    temperature: float = 0.0
    max_turns: int = 40
    max_tool_output_chars: int = 8000
    repeat_limit: int = 4
    deadline_sec: float | None = None

    @property
    def provider_name(self) -> str:
        return ProviderRegistry.resolve_spec(self.model)[0]

    @property
    def model_name(self) -> str:
        return ProviderRegistry.resolve_spec(self.model)[1]

    @property
    def model_spec(self) -> str:
        prov, m = ProviderRegistry.resolve_spec(self.model)
        return f"{prov}/{m}"

    def build_provider(self) -> ProviderAdapter:
        return build_provider(self.model, temperature=self.temperature)

    @classmethod
    def from_env(cls, model: str | None = None, **overrides: Any) -> AgentConfig:
        env_provider = os.environ.get("PROVIDER")
        env_model_name = os.environ.get("MODEL_NAME")
        env_model = model or os.environ.get("MODEL")
        if not env_model and env_provider:
            env_model = f"{env_provider}/{env_model_name}" if env_model_name else env_provider

        resolved_model = env_model or ProviderRegistry.default_spec()
        kwargs: dict[str, Any] = {"model": resolved_model}

        if "MAX_TURNS" in os.environ:
            kwargs["max_turns"] = int(os.environ["MAX_TURNS"])
        if "TEMPERATURE" in os.environ:
            kwargs["temperature"] = float(os.environ["TEMPERATURE"])
        if "PROMPT_ID" in os.environ:
            kwargs["prompt_id"] = os.environ["PROMPT_ID"]

        kwargs.update(overrides)
        return cls(**kwargs)
