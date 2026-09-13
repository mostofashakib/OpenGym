"""Controlled disturbances engine for Workstation simulation.

Injects seed-controlled runtime challenges (session drops, transient network errors,
conflicting edits, and incoming priority notifications) for studying recovery and replanning.
"""

from __future__ import annotations

import json
import os
import random
import sqlite3
from typing import Any


class DisturbanceError(Exception):
    """Custom exception raised when a simulated transient disturbance triggers."""

    def __init__(self, code: str, message: str, retryable: bool = True) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }


class DisturbanceManager:
    """Manages seeded, deterministic disturbances."""

    def __init__(self, seed: int = 42, disturbance_rate: float | None = None) -> None:
        self.seed = seed
        self.rng = random.Random(seed + 9999)
        env_rate = os.environ.get("WORKSTATION_DISTURBANCE_RATE")
        self.rate = float(env_rate) if env_rate is not None else (disturbance_rate if disturbance_rate is not None else 0.0)
        self.action_counter = 0

    def evaluate_action(
        self,
        application: str,
        action: str,
        conn: sqlite3.Connection | None = None,
    ) -> dict[str, Any] | None:
        """Check if a disturbance should interrupt this action.

        Returns None if normal execution should proceed, or raises DisturbanceError.
        """
        self.action_counter += 1
        if self.rate <= 0.0:
            return None

        roll = self.rng.random()
        if roll >= self.rate:
            return None

        # Determine disturbance type based on deterministic roll
        disturbance_type = self.rng.choice([
            "transient_network_timeout",
            "session_token_expired",
            "service_unavailable_503",
        ])

        if disturbance_type == "transient_network_timeout":
            raise DisturbanceError(
                code="network_timeout",
                message=f"Simulated network latency spike on {application}.{action}. Action timed out. Please retry.",
                retryable=True,
            )
        elif disturbance_type == "session_token_expired":
            raise DisturbanceError(
                code="session_expired",
                message=f"Authentication token for {application} has expired. Re-authenticate or retry to refresh credentials.",
                retryable=True,
            )
        elif disturbance_type == "service_unavailable_503":
            raise DisturbanceError(
                code="service_unavailable",
                message=f"Upstream application {application} temporarily unavailable (HTTP 503). Upstream circuit breaker open.",
                retryable=True,
            )

        return None
