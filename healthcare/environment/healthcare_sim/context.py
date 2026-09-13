"""Context and dependency injection container for the Healthcare environment."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .db_generator import create_dynamic_database
from .service import HealthcareService

DEFAULT_DB_PATH = Path("/var/lib/healthcare/hospital.db")


@dataclass
class HealthcareContext:
    """Dependency container managing healthcare simulation state and connections."""

    db_path: Path | str = DEFAULT_DB_PATH
    actor_id: str = "prac-001"
    actor_role: str = "physician"
    seed: int = 42

    def __post_init__(self) -> None:
        if isinstance(self.db_path, str):
            object.__setattr__(self, "db_path", Path(self.db_path))

    @property
    def service(self) -> HealthcareService:
        return HealthcareService(self.db_path)

    def get_connection(self):
        import sqlite3
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn


    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> HealthcareContext:
        env = os.environ if environ is None else environ
        if "HEALTHCARE_DB" in env:
            db_path = Path(env["HEALTHCARE_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "healthcare.db"

        actor_id = env.get("HEALTHCARE_ACTOR_ID", "prac-001")
        actor_role = env.get("HEALTHCARE_ACTOR_ROLE", "physician")
        seed = int(env.get("HEALTHCARE_SEED", "42"))
        return cls(db_path=db_path, actor_id=actor_id, actor_role=actor_role, seed=seed)

    def ensure_initialized(self) -> None:
        if not Path(self.db_path).exists():
            self.seed_database()

    def seed_database(self) -> Dict[str, Any]:
        if isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return create_dynamic_database(self.db_path, seed=self.seed)

    def seed_db(self) -> Dict[str, Any]:
        """Alias for seed_database."""
        return self.seed_database()

    def reset(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Reset and reseed database for a new episode."""
        if seed is not None:
            self.seed = seed
        db_p = Path(self.db_path)
        if db_p.exists():
            db_p.unlink()
        return self.seed_database()
