"""Command-line runner for the Gmail agent."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from agent.backends import HttpBackend, SubprocessBackend
from agent.config import AgentConfig
from agent.loop import ToolLoop
from agent.prompts import system_prompt
from agent.trajectory import build_trajectory, write_trajectory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Gmail agent locally.")
    parser.add_argument(
        "--model",
        default=None,
        help="Model specification, e.g. ollama/qwen3.6:35b, openrouter/anthropic/claude-opus-5",
    )
    parser.add_argument(
        "--instruction",
        default=None,
        help="Task instruction prompt (defaults to contents of instruction.md)",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:3000",
        help="Base URL of the running Gmail web app",
    )
    parser.add_argument(
        "--backend",
        choices=["http", "subprocess"],
        default="http",
        help="Tool execution backend",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("logs/agent"),
        help="Where to write trajectory.json",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=40,
        help="Maximum turns for the loop",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    instruction = args.instruction
    if not instruction:
        instruction_file = Path(__file__).resolve().parent.parent / "instruction.md"
        if instruction_file.is_file():
            instruction = instruction_file.read_text(encoding="utf-8").strip()
        else:
            instruction = "Review your inbox, mark unread emails as read, and star important emails."

    config = AgentConfig.from_env(model=args.model, max_turns=args.max_turns)
    provider = config.build_provider()

    if args.backend == "subprocess":
        backend = SubprocessBackend()
    else:
        backend = HttpBackend(base_url=args.base_url)

    loop = ToolLoop(
        provider,
        backend,
        system=system_prompt(config.prompt_id),
        max_turns=config.max_turns,
        max_tool_output_chars=config.max_tool_output_chars,
        repeat_limit=config.repeat_limit,
    )

    async def _run():
        return await loop.run(instruction)

    result = asyncio.run(_run())
    print("\n--- Agent Run Finished ---")
    print(f"Stop reason: {result.stop_reason}")
    print(f"Turns: {len(result.turns)}")
    print(f"Prompt tokens: {result.prompt_tokens}")
    print(f"Completion tokens: {result.completion_tokens}")

    trajectory = build_trajectory(
        result,
        agent_name="gmail-adapter",
        agent_version="1.0.0",
        model_name=provider.spec,
    )
    traj_path = args.logs_dir / "trajectory.json"
    write_trajectory(traj_path, trajectory)
    print(f"Wrote trajectory to {traj_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
