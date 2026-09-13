"""Context and dependency injection container for the Enterprise environment."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, Mapping, Optional

from .db_generator import create_enterprise_database
from .service import EnterpriseService

DEFAULT_DB_PATH = Path("/var/lib/enterprise/company.db")


@dataclass
class EnterpriseContext:
    """Dependency container managing enterprise digital twin state and service instances."""

    db_path: Path | str = DEFAULT_DB_PATH
    actor_id: str = "emp-003"
    actor_role_id: str = "role-mgr-supp"
    seed: int = 42

    def __post_init__(self) -> None:
        if isinstance(self.db_path, str):
            object.__setattr__(self, "db_path", Path(self.db_path))

    @property
    def service(self) -> EnterpriseService:
        return EnterpriseService(self.db_path, actor_id=self.actor_id, actor_role_id=self.actor_role_id)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> EnterpriseContext:
        env = os.environ if environ is None else environ
        if "ENTERPRISE_DB" in env:
            db_path = Path(env["ENTERPRISE_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "enterprise.db"

        actor_id = env.get("ENTERPRISE_ACTOR_ID", "emp-003")
        actor_role_id = env.get("ENTERPRISE_ACTOR_ROLE_ID", "role-mgr-supp")
        seed = int(env.get("ENTERPRISE_SEED", "42"))
        return cls(db_path=db_path, actor_id=actor_id, actor_role_id=actor_role_id, seed=seed)

    def ensure_initialized(self) -> None:
        if not Path(self.db_path).exists():
            self.seed_database()

    def seed_database(self) -> Dict[str, Any]:
        if isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return create_enterprise_database(self.db_path, seed=self.seed)

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
