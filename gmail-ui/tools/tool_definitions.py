"""Canonical model-facing tool definitions for the Gmail environment.

Re-exports the authoritative schemas defined in gmail_sim.tool_definitions.
"""

from __future__ import annotations

from gmail_sim.tool_definitions import (
    TOOL_DEFINITIONS,
    get_tool_definitions,
)

__all__ = ["TOOL_DEFINITIONS", "get_tool_definitions"]
