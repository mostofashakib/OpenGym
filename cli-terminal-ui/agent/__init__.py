"""Harbor agent and provider adapter framework for Terminal environment."""

from __future__ import annotations

from agent.config import AgentConfig
try:
    from agent.harbor_agent import TerminalAgent
except ImportError:  # pragma: no cover
    TerminalAgent = None  # type: ignore[assignment, misc]
from agent.loop import ToolLoop
from agent.providers import (
    AnthropicProvider,
    CompatibleAPIProvider,
    OllamaProvider,
    OpenRouterProvider,
    ProviderAdapter,
    ProviderAdapterRegistry,
    ProviderRegistry,
    build_provider,
    register_provider,
)
from agent.tracker import (
    ObservabilityTracker,
    ToolCallRecord,
    ToolStats,
    TurnRecord,
    get_tracker,
)

__all__ = [
    "AgentConfig",
    "AnthropicProvider",
    "CompatibleAPIProvider",
    "TerminalAgent",
    "ObservabilityTracker",
    "OllamaProvider",
    "OpenRouterProvider",
    "ProviderAdapter",
    "ProviderAdapterRegistry",
    "ProviderRegistry",
    "ToolCallRecord",
    "ToolLoop",
    "ToolStats",
    "TurnRecord",
    "build_provider",
    "get_tracker",
    "register_provider",
]
