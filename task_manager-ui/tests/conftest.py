from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path
import pytest


@pytest.fixture
def root() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory(dir="/tmp") as td:
        yield Path(td)


@pytest.fixture
def _root(root: Path) -> Path:
    return root
