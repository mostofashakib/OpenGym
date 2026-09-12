"""Observability tracker for agent evaluation, execution telemetry, and Harbor runs."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ToolCallRecord:
    id: str
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    latency_ms: float
    ok: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TurnRecord:
    turn_index: int
    start_iso: str
    end_iso: str | None = None
    duration_ms: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    llm_latency_ms: float = 0.0
    response_text: str = ""
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    stop_reason: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "start_iso": self.start_iso,
            "end_iso": self.end_iso,
            "duration_ms": round(self.duration_ms, 2),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "llm_latency_ms": round(self.llm_latency_ms, 2),
            "response_text": self.response_text,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "stop_reason": self.stop_reason,
            "error": self.error,
        }


@dataclass(slots=True)
class ToolStats:
    name: str
    call_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        return (self.total_latency_ms / self.call_count) if self.call_count else 0.0

    @property
    def success_rate(self) -> float:
        if not self.call_count:
            return 1.0
        return (self.call_count - self.error_count) / self.call_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "success_rate": round(self.success_rate, 4),
        }


class ObservabilityTracker:
    """Telemetry and execution observer for the agent run.

    Provides deep visibility into LLM calls, tool interactions, latencies,
    token counts, and lifecycle events across trials.
    """

    def __init__(
        self,
        session_id: str = "default",
        provider: str = "ollama",
        model: str = "qwen3.6:35b",
        agent_name: str = "gmail-adapter",
        agent_version: str = "1.0.0",
        logger: logging.Logger | None = None,
    ) -> None:
        self.session_id = session_id
        self.provider = provider
        self.model = model
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.logger = logger or logging.getLogger("agent.observability")

        self.start_iso: str = _iso_now()
        self.start_monotonic: float = time.monotonic()
        self.end_iso: str | None = None
        self.duration_sec: float = 0.0
        self.status: str = "running"
        self.stop_reason: str | None = None

        self.instruction: str = ""
        self.turns: list[TurnRecord] = []
        self._current_turn: TurnRecord | None = None
        self._turn_start_time: float = 0.0

        self.tool_stats: dict[str, ToolStats] = {}
        self.events: list[dict[str, Any]] = []

        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_llm_latency_ms: float = 0.0

        self.record_event("session_initialized", {
            "session_id": session_id,
            "provider": provider,
            "model": model,
        })

    def start_run(self, instruction: str) -> None:
        self.instruction = instruction
        self.record_event("run_started", {"instruction_len": len(instruction)})

    def record_event(self, name: str, payload: dict[str, Any] | None = None) -> None:
        event = {
            "timestamp": _iso_now(),
            "event": name,
            "payload": payload or {},
        }
        self.events.append(event)
        self.logger.debug("Observability event [%s]: %s", name, payload)

    def start_turn(self, turn_index: int) -> TurnRecord:
        self._turn_start_time = time.monotonic()
        turn = TurnRecord(
            turn_index=turn_index,
            start_iso=_iso_now(),
        )
        self._current_turn = turn
        self.record_event("turn_started", {"turn_index": turn_index})
        return turn

    def record_llm_call(
        self,
        turn_index: int,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        latency_sec: float,
        response_text: str = "",
        tool_calls: Sequence[Any] = (),
    ) -> None:
        latency_ms = latency_sec * 1000.0
        self.total_llm_latency_ms += latency_ms
        if prompt_tokens:
            self.total_prompt_tokens += prompt_tokens
        if completion_tokens:
            self.total_completion_tokens += completion_tokens

        if self._current_turn and self._current_turn.turn_index == turn_index:
            self._current_turn.llm_latency_ms = latency_ms
            self._current_turn.prompt_tokens = prompt_tokens
            self._current_turn.completion_tokens = completion_tokens
            self._current_turn.response_text = response_text

        self.record_event("llm_call_completed", {
            "turn_index": turn_index,
            "latency_ms": round(latency_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "tool_calls_count": len(tool_calls),
        })

    def record_tool_call(
        self,
        turn_index: int,
        call_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: dict[str, Any],
        latency_sec: float,
        ok: bool,
        error: str | None = None,
    ) -> ToolCallRecord:
        latency_ms = latency_sec * 1000.0

        if tool_name not in self.tool_stats:
            self.tool_stats[tool_name] = ToolStats(name=tool_name)
        stats = self.tool_stats[tool_name]
        stats.call_count += 1
        stats.total_latency_ms += latency_ms
        if not ok or error:
            stats.error_count += 1

        rec = ToolCallRecord(
            id=call_id,
            name=tool_name,
            arguments=arguments,
            result=result,
            latency_ms=latency_ms,
            ok=ok,
            error=error,
        )

        if self._current_turn and self._current_turn.turn_index == turn_index:
            self._current_turn.tool_calls.append(rec)

        self.record_event("tool_call_completed", {
            "turn_index": turn_index,
            "tool": tool_name,
            "latency_ms": round(latency_ms, 2),
            "ok": ok,
        })
        return rec

    def end_turn(
        self,
        turn_index: int,
        stop_reason: str | None = None,
        error: str | None = None,
    ) -> None:
        if self._current_turn and self._current_turn.turn_index == turn_index:
            now_mono = time.monotonic()
            self._current_turn.end_iso = _iso_now()
            self._current_turn.duration_ms = (now_mono - self._turn_start_time) * 1000.0
            self._current_turn.stop_reason = stop_reason
            self._current_turn.error = error
            self.turns.append(self._current_turn)
            self._current_turn = None

        self.record_event("turn_ended", {
            "turn_index": turn_index,
            "stop_reason": stop_reason,
            "error": error,
        })

    def finish_run(self, stop_reason: str = "completed") -> None:
        self.end_iso = _iso_now()
        self.duration_sec = time.monotonic() - self.start_monotonic
        self.status = "completed" if "error" not in stop_reason.lower() else "errored"
        self.stop_reason = stop_reason
        self.record_event("run_finished", {
            "status": self.status,
            "stop_reason": stop_reason,
            "duration_sec": round(self.duration_sec, 2),
        })

    def summary(self) -> dict[str, Any]:
        total_calls = sum(s.call_count for s in self.tool_stats.values())
        total_errors = sum(s.error_count for s in self.tool_stats.values())
        avg_turn_ms = (
            sum(t.duration_ms for t in self.turns) / len(self.turns)
            if self.turns
            else 0.0
        )
        return {
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "stop_reason": self.stop_reason,
            "duration_sec": round(self.duration_sec, 2),
            "total_turns": len(self.turns),
            "avg_turn_latency_ms": round(avg_turn_ms, 2),
            "total_llm_latency_ms": round(self.total_llm_latency_ms, 2),
            "tokens": {
                "prompt_tokens": self.total_prompt_tokens,
                "completion_tokens": self.total_completion_tokens,
                "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            },
            "tools": {
                "total_calls": total_calls,
                "error_calls": total_errors,
                "tool_breakdown": {
                    k: v.to_dict() for k, v in sorted(self.tool_stats.items())
                },
            },
            "events_count": len(self.events),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "Observability-v1.0",
            "metadata": {
                "session_id": self.session_id,
                "agent_name": self.agent_name,
                "agent_version": self.agent_version,
                "provider": self.provider,
                "model": self.model,
                "start_iso": self.start_iso,
                "end_iso": self.end_iso,
                "duration_sec": round(self.duration_sec, 3),
                "status": self.status,
                "stop_reason": self.stop_reason,
                "instruction": self.instruction,
            },
            "summary": self.summary(),
            "turns": [t.to_dict() for t in self.turns],
            "tool_stats": {k: v.to_dict() for k, v in self.tool_stats.items()},
            "events": self.events,
        }

    def export_json(self, target_path: str | Path, indent: int = 2) -> Path:
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=indent), encoding="utf-8")
        return path

    def render_ascii_dashboard(self) -> str:
        s = self.summary()
        lines = [
            "╔══════════════════════════════════════════════════════════════════════╗",
            f"║ OBSERVABILITY REPORT: {self.session_id:<46} ║",
            "╠══════════════════════════════════════════════════════════════════════╣",
            f"║ Model:    {self.provider + '/' + self.model:<58} ║",
            f"║ Status:   {self.status:<18} Stop Reason: {str(self.stop_reason):<26} ║",
            f"║ Duration: {self.duration_sec:<18.2f} Total Turns: {len(self.turns):<26} ║",
            f"║ Tokens:   In={self.total_prompt_tokens:<7} Out={self.total_completion_tokens:<7} Total={self.total_prompt_tokens + self.total_completion_tokens:<28} ║",
            "╟──────────────────────────────────────────────────────────────────────╢",
            "║ TOOL USAGE METRICS:                                                  ║",
        ]
        if not self.tool_stats:
            lines.append("║   (No tool calls recorded)                                           ║")
        else:
            for name, stats in sorted(self.tool_stats.items()):
                tool_line = f"  • {name:<20} calls: {stats.call_count:<4} err: {stats.error_count:<3} avg: {stats.avg_latency_ms:>6.1f}ms"
                lines.append(f"║ {tool_line:<68} ║")

        lines.append("╚══════════════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)


# Singleton factory helper
def get_tracker(
    session_id: str = "default",
    provider: str = "ollama",
    model: str = "qwen3.6:35b",
) -> ObservabilityTracker:
    return ObservabilityTracker(session_id=session_id, provider=provider, model=model)
