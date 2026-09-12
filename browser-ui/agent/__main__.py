"""CLI entry point for running the Browser agent."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from agent.backends import InProcessBackend
from agent.config import AgentConfig
from agent.loop import ToolLoop
from agent.prompts import system_prompt
from agent.tracker import ObservabilityTracker


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Browser Agent Runner")
    parser.add_argument("--model", default="ollama/qwen3.6:35b")
    parser.add_argument("--instruction-file", default="instruction.md")
    parser.add_argument("--db", default="/var/lib/browser/browser.db")
    args = parser.parse_args()

    inst_path = Path(args.instruction_file)
    instruction = inst_path.read_text(encoding="utf-8") if inst_path.exists() else "Audit procurement portal."

    config = AgentConfig.from_env(model=args.model)
    provider = config.build_provider()
    backend = InProcessBackend(args.db)
    tracker = ObservabilityTracker(session_id="cli", provider=provider.provider_name, model=provider.model)

    loop = ToolLoop(
        provider,
        backend,
        system=system_prompt(config.prompt_id),
        max_turns=config.max_turns,
        tracker=tracker,
    )
    res = await loop.run(instruction)
    print(f"Agent finished: turns={res.turns}, success={res.stop_reason}")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
