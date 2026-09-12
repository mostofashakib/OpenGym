"""LLM provider adapters.

One class per service, all speaking the same three-word vocabulary --
:class:`Message`, :class:`ToolCall`, :class:`Completion` -- so ``agent.loop``
never learns which service answered it. Adding a provider is a subclass;
no other module in this package changes.

Every call carries a schema, so the shape of what comes back is constrained before
generation rather than discovered afterwards.

Standard library only: no vendor SDKs required. Every endpoint is reached via
standard HTTP requests.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar

from agent.schemas import (
    ACTIONS_KEY,
    ANSWER_KEY,
    THOUGHT_KEY,
    build_action_schema,
    drop_nulls,
    normalize_tool_entry,
    render_catalogue,
    strict_parameters,
)

DEFAULT_TIMEOUT_SEC = 600.0

Message = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """One requested action, already decoded into arguments."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Completion:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    finish_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class ProviderError(RuntimeError):
    """The model could not be consulted."""


class ProviderUnavailable(ProviderError):
    """The endpoint could not be reached at all."""


class ProviderRejected(ProviderError):
    """The endpoint answered, and the answer was a refusal."""


def _post_json(
    url: str,
    payload: Mapping[str, Any],
    headers: Mapping[str, str],
    timeout_sec: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", "replace")
        raise ProviderRejected(
            f"HTTP {exc.code} from {url}: {err_body[:1000]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ProviderUnavailable(f"Could not reach {url}: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderUnavailable(f"{url} timed out or failed: {exc}") from exc


class ProviderAdapter(ABC):
    """Abstract base adapter for LLM providers."""

    output_mode: ClassVar[str] = "native"

    def __init__(
        self,
        model: str,
        *,
        temperature: float = 0.0,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.timeout_sec = timeout_sec

    @property
    def spec(self) -> str:
        return f"{self.provider_name}/{self.model}"

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The scheme prefix used in model strings."""

    @abstractmethod
    def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[Mapping[str, Any]] = (),
        system: str | None = None,
    ) -> Completion:
        """Send a turn to the model and return its Completion."""

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "spec": self.spec,
            "output_mode": self.output_mode,
            "temperature": self.temperature,
        }


_TAdapter = TypeVar("_TAdapter", bound=type[ProviderAdapter])


class ProviderAdapterRegistry:
    """Extensible registry and resolver for LLM provider adapters.

    Defaults to Ollama as the primary provider with easy provider switching.
    """

    DEFAULT_PROVIDER: ClassVar[str] = "ollama"
    DEFAULT_MODELS: ClassVar[dict[str, str]] = {
        "ollama": "qwen3.6:35b",
        "openrouter": "anthropic/claude-opus-5",
        "anthropic": "claude-3-5-sonnet-20241022",
        "compatible": "default",
        "local": "default",
        "generic": "default",
    }

    _registry: ClassVar[dict[str, type[ProviderAdapter]]] = {}

    @classmethod
    def register(cls, name: str, default_model: str | None = None) -> Any:
        """Decorator to register a provider adapter class."""
        def decorator(adapter_cls: _TAdapter) -> _TAdapter:
            cls.register_adapter(name, adapter_cls, default_model=default_model)
            return adapter_cls
        return decorator

    @classmethod
    def register_adapter(
        cls,
        name: str,
        adapter_cls: type[ProviderAdapter],
        default_model: str | None = None,
    ) -> None:
        key = name.lower().strip()
        cls._registry[key] = adapter_cls
        if default_model:
            cls.DEFAULT_MODELS[key] = default_model

    @classmethod
    def default_spec(cls, provider: str | None = None) -> str:
        prov = (provider or cls.DEFAULT_PROVIDER).lower().strip()
        model = cls.DEFAULT_MODELS.get(prov, cls.DEFAULT_MODELS[cls.DEFAULT_PROVIDER])
        return f"{prov}/{model}"

    @classmethod
    def resolve_spec(cls, spec_or_model: str | None) -> tuple[str, str]:
        """Resolve a model spec or provider alias into (provider, model).

        Resolution rules:
          - None or empty: (DEFAULT_PROVIDER, default model for DEFAULT_PROVIDER)
          - '<provider>/<model>': matches registered provider or treats as (DEFAULT_PROVIDER, spec)
          - '<provider>' (registered provider name): (provider, default model for provider)
          - '<bare_model>': (DEFAULT_PROVIDER, bare_model)
        """
        raw = (spec_or_model or "").strip()
        if not raw:
            prov = cls.DEFAULT_PROVIDER
            return (prov, cls.DEFAULT_MODELS[prov])

        if "/" in raw:
            prefix, remainder = raw.split("/", 1)
            prefix_lower = prefix.lower()
            if prefix_lower in cls._registry:
                return (prefix_lower, remainder)
            # If prefix isn't known but has slashes, check if it's openrouter format e.g. openrouter/...
            for reg_name in cls._registry:
                if raw.lower().startswith(f"{reg_name}/"):
                    return (reg_name, raw[len(reg_name) + 1:])
            # Fallback to default provider with the raw model string
            return (cls.DEFAULT_PROVIDER, raw)

        raw_lower = raw.lower()
        if raw_lower in cls._registry:
            return (raw_lower, cls.DEFAULT_MODELS.get(raw_lower, "default"))

        # Bare model without slash defaults to Ollama
        return (cls.DEFAULT_PROVIDER, raw)

    @classmethod
    def create(cls, spec_or_model: str | None = None, **kwargs: Any) -> ProviderAdapter:
        """Instantiate the registered provider adapter for the spec or alias."""
        provider_name, model_name = cls.resolve_spec(spec_or_model)
        adapter_cls = cls._registry.get(provider_name)
        if not adapter_cls:
            available = ", ".join(sorted(cls._registry.keys()))
            raise ValueError(
                f"Unknown provider adapter '{provider_name}'. Available providers: {available}"
            )
        return adapter_cls(model=model_name, **kwargs)

    @classmethod
    def available_providers(cls) -> list[str]:
        return sorted(cls._registry.keys())


# Alias for concise usage
ProviderRegistry = ProviderAdapterRegistry
register_provider = ProviderAdapterRegistry.register


@register_provider("ollama", default_model="qwen3.6:35b")
class OllamaProvider(ProviderAdapter):
    """Adapter for local Ollama instances."""

    output_mode: ClassVar[str] = "schema"

    def __init__(
        self,
        model: str,
        *,
        base_url: str | None = None,
        temperature: float = 0.0,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    ) -> None:
        super().__init__(model, temperature=temperature, timeout_sec=timeout_sec)
        env_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.base_url = (base_url or env_host).rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[Mapping[str, Any]] = (),
        system: str | None = None,
    ) -> Completion:
        norm_tools = [normalize_tool_entry(t) for t in tools]
        schema = build_action_schema(norm_tools)
        system_text = (system or "").strip()
        if norm_tools:
            catalogue = render_catalogue(norm_tools)
            system_text = f"{system_text}\n\n{catalogue}".strip()

        formatted_messages: list[dict[str, Any]] = []
        if system_text:
            formatted_messages.append({"role": "system", "content": system_text})

        for msg in messages:
            if isinstance(msg, Mapping):
                role = msg.get("role", "user")
                content = str(msg.get("content", ""))
                tool_name = str(msg.get("name", "tool"))
            else:
                role = "user"
                content = str(msg)
                tool_name = "tool"
            if role == "tool":
                formatted_messages.append({
                    "role": "user",
                    "content": f"[Result of {tool_name}]: {content}",
                })
            elif role == "assistant":
                formatted_messages.append({
                    "role": "assistant",
                    "content": content,
                })
            else:
                formatted_messages.append({
                    "role": "user",
                    "content": content,
                })

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "format": schema,
            "stream": False,
            "options": {"temperature": self.temperature},
        }

        url = f"{self.base_url}/api/chat"
        response = _post_json(url, payload, {}, self.timeout_sec)

        message = response.get("message") or {}
        content_text = message.get("content", "").strip()

        prompt_tokens = response.get("prompt_eval_count")
        completion_tokens = response.get("eval_count")

        tool_calls: list[ToolCall] = []
        answer_text = content_text

        if content_text:
            try:
                parsed = json.loads(content_text)
                if isinstance(parsed, dict):
                    actions = parsed.get(ACTIONS_KEY, [])
                    if isinstance(actions, list):
                        for idx, act in enumerate(actions):
                            if isinstance(act, dict) and "tool" in act:
                                tool_calls.append(
                                    ToolCall(
                                        id=f"ollama_{idx}",
                                        name=act["tool"],
                                        arguments=act.get("arguments") or {},
                                    )
                                )
                    answer_text = parsed.get(ANSWER_KEY, "") or parsed.get(THOUGHT_KEY, "")
            except json.JSONDecodeError:
                pass

        return Completion(
            text=answer_text,
            tool_calls=tuple(tool_calls),
            finish_reason="stop",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


@register_provider("compatible", default_model="default")
class CompatibleAPIProvider(ProviderAdapter):
    """Adapter for standard HTTP JSON chat completions endpoints."""

    output_mode: ClassVar[str] = "native"

    def __init__(
        self,
        model: str,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    ) -> None:
        super().__init__(model, temperature=temperature, timeout_sec=timeout_sec)
        self.base_url = (base_url or os.environ.get("COMPATIBLE_API_BASE", "http://127.0.0.1:8000/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("COMPATIBLE_API_KEY", "")

    @property
    def provider_name(self) -> str:
        return "compatible"

    def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[Mapping[str, Any]] = (),
        system: str | None = None,
    ) -> Completion:
        formatted_messages: list[dict[str, Any]] = []
        if system:
            formatted_messages.append({"role": "system", "content": system})

        for msg in messages:
            formatted_messages.append(dict(msg))

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature,
        }

        if tools:
            formatted_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": strict_parameters(tool.get("input_schema")),
                        "strict": True,
                    },
                }
                for tool in (normalize_tool_entry(t) for t in tools)
            ]
            payload["tools"] = formatted_tools

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/chat/completions"
        response = _post_json(url, payload, headers, self.timeout_sec)

        choices = response.get("choices") or [{}]
        first = choices[0]
        msg = first.get("message") or {}
        content = msg.get("content") or ""
        finish_reason = first.get("finish_reason")

        raw_tool_calls = msg.get("tool_calls") or []
        parsed_tool_calls: list[ToolCall] = []
        for tc in raw_tool_calls:
            fn = tc.get("function") or {}
            args_str = fn.get("arguments") or "{}"
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                args = {}
            parsed_tool_calls.append(
                ToolCall(
                    id=tc.get("id", f"call_{len(parsed_tool_calls)}"),
                    name=fn.get("name", ""),
                    arguments=args,
                )
            )

        usage = response.get("usage") or {}
        return Completion(
            text=content,
            tool_calls=tuple(parsed_tool_calls),
            finish_reason=finish_reason,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )


@register_provider("openrouter", default_model="anthropic/claude-opus-5")
class OpenRouterProvider(CompatibleAPIProvider):
    """Adapter for models served via OpenRouter."""

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        temperature: float = 0.0,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    ) -> None:
        key = api_key or os.environ.get("OPEN_ROUTER_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
        super().__init__(
            model,
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
            temperature=temperature,
            timeout_sec=timeout_sec,
        )

    @property
    def provider_name(self) -> str:
        return "openrouter"


@register_provider("anthropic", default_model="claude-3-5-sonnet-20241022")
class AnthropicProvider(ProviderAdapter):
    """Adapter for Anthropic Claude models."""

    output_mode: ClassVar[str] = "native"

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.0,
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    ) -> None:
        super().__init__(model, temperature=temperature, timeout_sec=timeout_sec)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.base_url = (base_url or "https://api.anthropic.com/v1").rstrip("/")

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[Mapping[str, Any]] = (),
        system: str | None = None,
    ) -> Completion:
        formatted_messages: list[dict[str, Any]] = []
        for msg in messages:
            role = msg["role"]
            if role == "tool":
                formatted_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg["tool_call_id"],
                            "content": msg["content"],
                        }
                    ],
                })
            elif role == "assistant" and msg.get("tool_calls"):
                content_blocks: list[dict[str, Any]] = []
                if msg.get("content"):
                    content_blocks.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    call_id = tc.id if isinstance(tc, ToolCall) else tc["id"]
                    name = tc.name if isinstance(tc, ToolCall) else tc["name"]
                    args = tc.arguments if isinstance(tc, ToolCall) else tc["arguments"]
                    content_blocks.append({
                        "type": "tool_use",
                        "id": call_id,
                        "name": name,
                        "input": args,
                    })
                formatted_messages.append({"role": "assistant", "content": content_blocks})
            else:
                formatted_messages.append({
                    "role": "user" if role == "user" else "assistant",
                    "content": msg.get("content", ""),
                })

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": 4096,
            "temperature": self.temperature,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [
                {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("input_schema") or {"type": "object"},
                }
                for tool in (normalize_tool_entry(t) for t in tools)
            ]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        url = f"{self.base_url}/messages"
        response = _post_json(url, payload, headers, self.timeout_sec)

        content_blocks = response.get("content") or []
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.get("id", ""),
                        name=block.get("name", ""),
                        arguments=block.get("input") or {},
                    )
                )

        usage = response.get("usage") or {}
        return Completion(
            text="\n".join(text_parts).strip(),
            tool_calls=tuple(tool_calls),
            finish_reason=response.get("stop_reason"),
            prompt_tokens=usage.get("input_tokens"),
            completion_tokens=usage.get("output_tokens"),
        )


# Register provider aliases for compatible HTTP endpoints
ProviderRegistry.register_adapter("local", CompatibleAPIProvider)
ProviderRegistry.register_adapter("generic", CompatibleAPIProvider)


def build_provider(model_spec: str | None = None, **kwargs: Any) -> ProviderAdapter:
    """Instantiate a provider adapter using the adapter registry.

    Defaults to Ollama (qwen3.6:35b) when unspecified, and seamlessly adapts
    to any registered provider or model spec:
      - 'ollama/qwen3.6:35b' or 'qwen3.6:35b' -> OllamaProvider('qwen3.6:35b')
      - 'openrouter/anthropic/claude-opus-5' -> OpenRouterProvider('anthropic/claude-opus-5')
      - 'anthropic/claude-3-5-sonnet' -> AnthropicProvider('claude-3-5-sonnet')
      - 'compatible/my-model' -> CompatibleAPIProvider('my-model')
    """
    return ProviderAdapterRegistry.create(model_spec, **kwargs)
