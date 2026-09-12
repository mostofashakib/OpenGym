"""Harbor agent and provider adapter framework for Browser environment."""

from __future__ import annotations

from agent.config import AgentConfig
try:
    from agent.harbor_agent import BrowserAgent
except ImportError:  # pragma: no cover
    BrowserAgent = None  # type: ignore[assignment, misc]
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
    "BrowserAgent",
    "CompatibleAPIProvider",
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
