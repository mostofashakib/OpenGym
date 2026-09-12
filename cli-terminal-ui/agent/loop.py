"""The provider-agnostic agent tool loop with adapter architecture and observability."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from agent.backends import HttpBackend, ToolBackend
from agent.providers import (
    Completion,
    Message,
    ProviderAdapter,
    ToolCall,
    build_provider,
)
from agent.tracker import ObservabilityTracker


@dataclass(slots=True)
class TurnResult:
    turn_index: int
    text: str
    tool_calls: tuple[ToolCall, ...] = ()
    results: tuple[dict[str, Any], ...] = ()
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    duration_ms: float = 0.0

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


@dataclass(slots=True)
class RunResult:
    instruction: str
    turns: list[TurnResult] = field(default_factory=list)
    stop_reason: str = "completed"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_sec: float = 0.0

    @property
    def total_tool_calls(self) -> int:
        return sum(len(t.tool_calls) for t in self.turns)

    @property
    def last_answer(self) -> str:
        for t in reversed(self.turns):
            if t.text:
                return t.text
        return ""

    def summary(self) -> dict[str, Any]:
        return {
            "turns": len(self.turns),
            "stop_reason": self.stop_reason,
            "duration_sec": round(self.duration_sec, 3),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "total_tool_calls": self.total_tool_calls,
        }


class ToolLoop:
    """Orchestrates conversations between an LLM provider adapter and a tool backend."""

    def __init__(
        self,
        provider: ProviderAdapter | str | None = None,
        backend: ToolBackend | None = None,
        *,
        system: str | None = None,
        max_turns: int = 40,
        max_tool_output_chars: int = 8000,
        repeat_limit: int = 4,
        deadline_sec: float | None = None,
        logger: logging.Logger | None = None,
        tracker: ObservabilityTracker | None = None,
    ) -> None:
        # Resolve provider adapter: defaults to Ollama when None or string spec
        if isinstance(provider, str) or provider is None:
            self.provider: ProviderAdapter = build_provider(provider)
        else:
            self.provider = provider

        self.backend: ToolBackend = backend if backend is not None else HttpBackend()
        self.system = system
        self.max_turns = max_turns
        self.max_tool_output_chars = max_tool_output_chars
        self.repeat_limit = repeat_limit
        self.deadline_sec = deadline_sec
        self.logger = logger or logging.getLogger("agent.loop")
        self.tracker = tracker or ObservabilityTracker(
            provider=self.provider.provider_name,
            model=self.provider.model,
            logger=self.logger,
        )

    async def run(self, instruction: str) -> RunResult:
        start_time = time.monotonic()
        self.tracker.start_run(instruction)
        try:
            tools = await self.backend.list_tools()
        except Exception as exc:
            self.logger.warning("Could not list tools from backend: %s", exc)
            tools = []
        messages: list[Message] = [{"role": "user", "content": instruction}]
        result = RunResult(instruction=instruction)

        seen_calls: dict[str, int] = {}
        turn_idx = 0

        for turn_idx in range(1, self.max_turns + 1):
            if self.deadline_sec and (time.monotonic() - start_time) > self.deadline_sec:
                result.stop_reason = "deadline_exceeded"
                self.tracker.record_event("deadline_exceeded", {"turn_index": turn_idx})
                break

            turn_t0 = time.monotonic()
            self.tracker.start_turn(turn_idx)
            llm_t0 = time.monotonic()
            try:
                completion: Completion = await asyncio.to_thread(
                    self.provider.complete,
                    messages,
                    tools=tools,
                    system=self.system,
                )
                llm_lat = time.monotonic() - llm_t0
            except Exception as exc:
                llm_lat = time.monotonic() - llm_t0
                self.logger.error("Provider call failed on turn %d: %s", turn_idx, exc, exc_info=True)
                result.stop_reason = f"provider_error: {exc}"
                self.tracker.record_llm_call(
                    turn_index=turn_idx,
                    prompt_tokens=None,
                    completion_tokens=None,
                    latency_sec=llm_lat,
                    response_text="",
                    tool_calls=(),
                )
                self.tracker.end_turn(turn_idx, stop_reason=result.stop_reason, error=str(exc))
                break

            self.tracker.record_llm_call(
                turn_index=turn_idx,
                prompt_tokens=completion.prompt_tokens,
                completion_tokens=completion.completion_tokens,
                latency_sec=llm_lat,
                response_text=completion.text,
                tool_calls=completion.tool_calls,
            )

            if completion.prompt_tokens:
                result.prompt_tokens += completion.prompt_tokens
            if completion.completion_tokens:
                result.completion_tokens += completion.completion_tokens

            # If no tool calls were made, the agent finished its task
            if not completion.tool_calls:
                turn_dur = (time.monotonic() - turn_t0) * 1000.0
                turn = TurnResult(
                    turn_index=turn_idx,
                    text=completion.text,
                    prompt_tokens=completion.prompt_tokens,
                    completion_tokens=completion.completion_tokens,
                    duration_ms=turn_dur,
                )
                result.turns.append(turn)
                result.stop_reason = "finished"
                self.tracker.end_turn(turn_idx, stop_reason="finished")
                break

            # Execute tool calls
            tool_results: list[dict[str, Any]] = []
            assistant_msg: Message = {
                "role": "assistant",
                "content": completion.text or "",
                "tool_calls": [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in completion.tool_calls
                ],
            }
            messages.append(assistant_msg)

            repeated = False
            for tc in completion.tool_calls:
                sig = f"{tc.name}:{json.dumps(tc.arguments, sort_keys=True)}"
                seen_calls[sig] = seen_calls.get(sig, 0) + 1
                if seen_calls[sig] > self.repeat_limit:
                    repeated = True

                self.logger.info("Calling tool %s: %s", tc.name, tc.arguments)
                tool_t0 = time.monotonic()
                try:
                    envelope = await self.backend.call(tc.name, tc.arguments)
                    tool_lat = time.monotonic() - tool_t0
                    ok = bool(envelope.get("ok", True))
                    err = str(envelope.get("error")) if not ok else None
                except Exception as exc:
                    tool_lat = time.monotonic() - tool_t0
                    envelope = {"ok": False, "error": str(exc)}
                    ok = False
                    err = str(exc)

                self.tracker.record_tool_call(
                    turn_index=turn_idx,
                    call_id=tc.id,
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    result=envelope,
                    latency_sec=tool_lat,
                    ok=ok,
                    error=err,
                )

                tool_results.append(envelope)
                res_text = json.dumps(envelope, sort_keys=True, default=str)
                if len(res_text) > self.max_tool_output_chars:
                    res_text = res_text[: self.max_tool_output_chars] + "... [truncated]"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": res_text,
                })

            turn_dur = (time.monotonic() - turn_t0) * 1000.0
            turn = TurnResult(
                turn_index=turn_idx,
                text=completion.text,
                tool_calls=completion.tool_calls,
                results=tuple(tool_results),
                prompt_tokens=completion.prompt_tokens,
                completion_tokens=completion.completion_tokens,
                duration_ms=turn_dur,
            )
            result.turns.append(turn)

            # Check for terminal action submit_task
            for tc in completion.tool_calls:
                if tc.name == "submit_task":
                    result.stop_reason = "task_submitted"
                    result.duration_sec = time.monotonic() - start_time
                    self.tracker.end_turn(turn_idx, stop_reason="task_submitted")
                    self.tracker.finish_run(result.stop_reason)
                    return result

            if repeated:
                result.stop_reason = "repeat_limit_exceeded"
                self.tracker.end_turn(turn_idx, stop_reason="repeat_limit_exceeded")
                break

            self.tracker.end_turn(turn_idx)

        if turn_idx >= self.max_turns and result.stop_reason == "completed":
            result.stop_reason = "max_turns_reached"

        result.duration_sec = time.monotonic() - start_time
        self.tracker.finish_run(result.stop_reason)
        return result


if __name__ == "__main__":
    import sys
    from agent.__main__ import main

    sys.exit(main())
