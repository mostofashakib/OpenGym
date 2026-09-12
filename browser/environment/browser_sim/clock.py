"""Virtual clock for the browser environment."""

from __future__ import annotations

DEFAULT_START_TIME = 1773360000.0


class VirtualClock:
    def __init__(self, current_time: float = DEFAULT_START_TIME) -> None:
        self._time = current_time

    def now(self) -> float:
        return self._time

    def advance(self, seconds: float = 1.0) -> float:
        self._time += seconds
        return self._time

    def reset(self, new_time: float = DEFAULT_START_TIME) -> None:
        self._time = new_time


VIRTUAL_CLOCK = VirtualClock()
