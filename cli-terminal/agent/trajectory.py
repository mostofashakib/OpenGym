"""Write a run out as ATIF, the trajectory format Harbor reads."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "ATIF-v1.7"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def build_trajectory(
    result: Any,
    *,
    agent_name: str,
    agent_version: str,
    model_name: str,
    tool_definitions: list[dict[str, Any]] | None = None,
    session_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = [
        {
            "step_id": 1,
            "timestamp": _now(),
            "source": "user",
            "message": result.instruction,
        }
    ]
    for turn in result.turns:
        step: dict[str, Any] = {
            "step_id": len(steps) + 1,
            "timestamp": _now(),
            "source": "agent",
            "model_name": model_name,
            "message": turn.text,
            "llm_call_count": 1,
        }
        if turn.tool_calls:
            step["tool_calls"] = [
                {
                    "tool_call_id": call.id,
                    "function_name": call.name,
                    "arguments": call.arguments,
                }
                for call in turn.tool_calls
            ]
            step["observation"] = {
                "results": [
                    {
                        "source_call_id": call.id,
                        "content": json.dumps(envelope, sort_keys=True, default=str),
                    }
                    for call, envelope in zip(turn.tool_calls, turn.results, strict=False)
                ]
            }
        metrics = {
            key: value
            for key, value in (
                ("prompt_tokens", turn.prompt_tokens),
                ("completion_tokens", turn.completion_tokens),
            )
            if value is not None
        }
        if metrics:
            step["metrics"] = metrics
        steps.append(step)

    trajectory: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "agent": {
            "name": agent_name,
            "version": agent_version,
            "model_name": model_name,
        },
        "steps": steps,
        "final_metrics": {
            "total_prompt_tokens": result.prompt_tokens,
            "total_completion_tokens": result.completion_tokens,
            "total_steps": len(steps),
        },
        "extra": {"stop_reason": result.stop_reason, **(extra or {})},
    }
    if session_id:
        trajectory["session_id"] = session_id
    if tool_definitions:
        trajectory["tools"] = tool_definitions
    return trajectory


def write_trajectory(path: Path | str, trajectory: dict[str, Any]) -> None:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        json.dump(trajectory, f, indent=2, ensure_ascii=False)
