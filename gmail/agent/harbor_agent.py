"""Harbor entry point for Gmail agent.

    harbor run -p OpenGym/gmail-ui -a agent.harbor_agent:GmailAgent -m ollama/qwen3.6:35b

Translates between Harbor's agent protocol and the plain loop in :mod:`agent.loop`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from harbor.agents.base import BaseAgent
    from harbor.environments.base import BaseEnvironment
    from harbor.models.agent.context import AgentContext
except ImportError:
    class BaseAgent:  # type: ignore[no-redef]
        def __init__(self, logs_dir: Path | None = None, model_name: str | None = None, *args: Any, **kwargs: Any) -> None:
            self.logs_dir = Path(logs_dir) if logs_dir else Path(".")
            self.model_name = model_name

    class BaseEnvironment:  # type: ignore[no-redef]
        pass

    class AgentContext:  # type: ignore[no-redef]
        pass

from agent.backends import HarborBackend
from agent.config import AgentConfig
from agent.loop import ToolLoop
from agent.prompts import system_prompt
from agent.tracker import ObservabilityTracker
from agent.trajectory import build_trajectory, write_trajectory

AGENT_NAME = "gmail-adapter"
AGENT_VERSION = "1.0.0"


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class GmailAgent(BaseAgent):
    """Drive Gmail tasks with whichever provider `-m` specifies."""

    SUPPORTS_ATIF = True

    def __init__(
        self,
        logs_dir: Path,
        model_name: str | None = None,
        *args: Any,
        agent_timeout_sec: float | None = None,
        **kwargs: Any,
    ) -> None:
        config_fields = {field.name for field in AgentConfig.__dataclass_fields__.values()}
        overrides = {key: kwargs.pop(key) for key in list(kwargs) if key in config_fields}
        super().__init__(logs_dir=logs_dir, model_name=model_name, *args, **kwargs)
        self._agent_timeout_sec = agent_timeout_sec
        self._config = self._build_config(model_name, overrides)
        self._provider = self._config.build_provider()
        self._result: Any = None

        # Pre-seed minimal valid ATIF trajectory.json using the resolved adapter spec
        try:
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            traj_path = self.logs_dir / "trajectory.json"
            if not traj_path.exists():
                traj_path.write_text(
                    json.dumps({
                        "schema_version": "ATIF-v1.7",
                        "session_id": getattr(self, "session_id", "default"),
                        "agent": {"name": AGENT_NAME, "version": AGENT_VERSION},
                        "model_name": self._provider.spec,
                        "steps": [],
                    }, indent=2)
                )
        except Exception as exc:
            self.logger.warning("Could not pre-seed trajectory.json: %s", exc)

    def _build_config(self, model_name: str | None, overrides: dict[str, Any]) -> AgentConfig:
        typed: dict[str, Any] = {}
        for key, value in overrides.items():
            field = AgentConfig.__dataclass_fields__[key]
            annotation = str(field.type)
            if "bool" in annotation:
                typed[key] = _as_bool(value)
            elif "int" in annotation:
                typed[key] = int(value)
            elif "float" in annotation:
                typed[key] = float(value)
            else:
                typed[key] = value
        if self._agent_timeout_sec and "deadline_sec" not in typed:
            typed["deadline_sec"] = max(30.0, float(self._agent_timeout_sec) - 30.0)
        return AgentConfig.from_env(model=model_name, **typed)

    @staticmethod
    def name() -> str:
        return AGENT_NAME

    def version(self) -> str:
        return AGENT_VERSION

    async def setup(self, environment: BaseEnvironment) -> None:
        return None

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        provider = self._provider
        tracker = ObservabilityTracker(
            session_id=getattr(self, "session_id", "default"),
            provider=provider.provider_name,
            model=provider.model,
            agent_name=AGENT_NAME,
            agent_version=AGENT_VERSION,
            logger=self.logger,
        )

        backend = HarborBackend(environment)
        self.logger.info(
            "gmail-adapter: %s via %s", provider.spec, backend.describe()["backend"]
        )

        loop = ToolLoop(
            provider,
            backend,
            system=system_prompt(self._config.prompt_id),
            max_turns=self._config.max_turns,
            max_tool_output_chars=self._config.max_tool_output_chars,
            repeat_limit=self._config.repeat_limit,
            deadline_sec=self._config.deadline_sec,
            logger=self.logger,
            tracker=tracker,
        )
        try:
            tools = await backend.list_tools()
        except Exception:
            tools = []

        result = await loop.run(instruction)
        self._result = result

        context.n_input_tokens = result.prompt_tokens or None
        context.n_output_tokens = result.completion_tokens or None
        context.metadata = {
            **provider.describe(),
            **backend.describe(),
            **result.summary(),
            "observability": tracker.summary(),
        }

        # Write ATIF trajectory
        write_trajectory(
            self.logs_dir / "trajectory.json",
            build_trajectory(
                result,
                agent_name=AGENT_NAME,
                agent_version=AGENT_VERSION,
                model_name=provider.spec,
                tool_definitions=tools or None,
                session_id=self.session_id,
                extra=provider.describe(),
            ),
        )

        # Export observability telemetry
        try:
            obs_path = self.logs_dir / "observability.json"
            tracker.export_json(obs_path)
            self.logger.info("\n" + tracker.render_ascii_dashboard())
        except Exception as exc:
            self.logger.warning("Could not export observability.json: %s", exc)

        self.logger.info("gmail-adapter finished: %s", result.summary())


# Alias for compatibility with Harbor harnesses expecting WorkspaceAgent
WorkspaceAgent = GmailAgent

