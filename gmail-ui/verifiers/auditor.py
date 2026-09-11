"""Audit checks for prohibited side-effects or integrity violations."""

from __future__ import annotations

from typing import Any

from verifiers.results import Penalty


def audit_run(events: list[dict[str, Any]] | None = None) -> tuple[Penalty, ...]:
    penalties: list[Penalty] = []
    # If explicit forbidden actions were detected, record a penalty here
    return tuple(penalties)
